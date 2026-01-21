import { apiGet } from '../api.js';
import {
    html, litRender, nothing,
    getConfig, typeEmoji, formatDateTime, formatDateTimeShort,
    truncateKey, errorAlert,
    pagination, createFilterHandler, autoSubmit, submitOnEnter
} from '../components.js';

export async function render(container, params, router) {
    const query = params.query || {};
    const search = query.search || '';
    const public_key = query.public_key || '';
    const member_id = query.member_id || '';
    const page = parseInt(query.page, 10) || 1;
    const limit = parseInt(query.limit, 10) || 20;
    const offset = (page - 1) * limit;

    const config = getConfig();
    const tz = config.timezone || '';
    const tzBadge = tz && tz !== 'UTC' ? html`<span class="text-sm opacity-60">${tz}</span>` : nothing;
    const navigate = (url) => router.navigate(url);
    let advertisements = [];
    let total = 0;
    let sortedNodes = [];
    let members = [];
    let socket = null;
    let retryDelay = 1000;
    let closed = false;

    function renderPage(content, { total = null } = {}) {
        litRender(html`
<div class="flex items-center justify-between mb-6">
    <h1 class="text-3xl font-bold">Advertisements</h1>
    <div class="flex items-center gap-2">
        ${tzBadge}
        ${total !== null ? html`<span class="badge badge-lg">${total} total</span>` : nothing}
    </div>
</div>
${content}`, container);
    }

    const buildWebSocketUrl = () => {
        const url = new URL('/api/v1/ws/events', window.location.origin);
        url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
        return url.toString();
    };

    const matchesFilters = (ad) => {
        if (public_key && ad.public_key !== public_key) {
            return false;
        }
        if (member_id) {
            return false;
        }
        if (!search) {
            return true;
        }
        const haystack = [ad.public_key, ad.name, ad.node_name, ad.node_tag_name]
            .filter(Boolean)
            .map((value) => value.toLowerCase());
        return haystack.some((value) => value.includes(search.toLowerCase()));
    };

    const findRecentAdIndex = (publicKey, receivedAt, windowSeconds = 10) => {
        if (!publicKey || !receivedAt) {
            return -1;
        }
        const newTimestamp = new Date(receivedAt).getTime();
        if (Number.isNaN(newTimestamp)) {
            return -1;
        }
        for (let i = 0; i < advertisements.length; i += 1) {
            const candidate = advertisements[i];
            if (!candidate || candidate.public_key !== publicKey || !candidate.received_at) {
                continue;
            }
            const existingTimestamp = new Date(candidate.received_at).getTime();
            if (Number.isNaN(existingTimestamp)) {
                continue;
            }
            const diffSeconds = Math.abs(newTimestamp - existingTimestamp) / 1000;
            if (diffSeconds <= windowSeconds) {
                return i;
            }
        }
        return -1;
    };

    const handleRealtimeEvent = (eventData) => {
        if (!eventData || eventData.event_name !== 'advertisement') {
            return;
        }

        const payload = eventData.payload || {};
        if (!payload.public_key) {
            return;
        }

        const advertisement = {
            public_key: payload.public_key,
            name: payload.name || null,
            node_name: payload.node_name || null,
            node_tag_name: payload.node_tag_name || null,
            adv_type: payload.adv_type || null,
            flags: payload.flags ?? null,
            received_at: eventData.received_at || new Date().toISOString(),
            receivers: [],
            received_by: eventData.public_key || null,
            receiver_name: null,
            receiver_tag_name: null,
        };

        if (!matchesFilters(advertisement)) {
            return;
        }

        const existingIndex = findRecentAdIndex(advertisement.public_key, advertisement.received_at);
        if (existingIndex >= 0) {
            const existing = advertisements[existingIndex];
            if (existing) {
                existing.received_at = advertisement.received_at;
                if (advertisement.received_by) {
                    if (!Array.isArray(existing.receivers)) {
                        existing.receivers = [];
                    }
                    const receiverExists = existing.receivers.some(
                        (receiver) => receiver.public_key === advertisement.received_by
                    );
                    if (!receiverExists) {
                        existing.receivers.push({
                            public_key: advertisement.received_by,
                        });
                    }
                }
                advertisements[existingIndex] = { ...existing };
            }
            renderContent();
            return;
        }

        advertisements = [advertisement, ...advertisements];
        if (advertisements.length > limit) {
            advertisements = advertisements.slice(0, limit);
        }
        total += 1;
        renderContent();
    };

    const startWebSocket = () => {
        const connect = () => {
            if (closed) return;
            const url = buildWebSocketUrl();
            socket = new WebSocket(url);

            socket.onopen = () => {
                retryDelay = 1000;
            };

            socket.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    handleRealtimeEvent(data);
                } catch (err) {
                    console.warn('Failed to parse event payload', err);
                }
            };

            socket.onclose = () => {
                if (closed) return;
                setTimeout(connect, Math.min(retryDelay, 10000));
                retryDelay = Math.min(retryDelay * 2, 10000);
            };

            socket.onerror = () => {
                if (socket) socket.close();
            };
        };

        connect();
    };

    function renderContent() {
        const totalPages = Math.ceil(total / limit);
        const nodesFilter = sortedNodes.length > 0
            ? html`
            <div class="form-control">
                <label class="label py-1">
                    <span class="label-text">Node</span>
                </label>
                <select name="public_key" class="select select-bordered select-sm" @change=${autoSubmit}>
                    <option value="">All Nodes</option>
                    ${sortedNodes.map(n => html`<option value=${n.public_key} ?selected=${public_key === n.public_key}>${n._displayName}</option>`)}
                </select>
            </div>`
            : nothing;

        const membersFilter = members.length > 0
            ? html`
            <div class="form-control">
                <label class="label py-1">
                    <span class="label-text">Member</span>
                </label>
                <select name="member_id" class="select select-bordered select-sm" @change=${autoSubmit}>
                    <option value="">All Members</option>
                    ${members.map(m => html`<option value=${m.member_id} ?selected=${member_id === m.member_id}>${m.name}${m.callsign ? ` (${m.callsign})` : ''}</option>`)}
                </select>
            </div>`
            : nothing;

        const mobileCards = advertisements.length === 0
            ? html`<div class="text-center py-8 opacity-70">No advertisements found.</div>`
            : advertisements.map(ad => {
                const emoji = typeEmoji(ad.adv_type);
                const adName = ad.node_tag_name || ad.node_name || ad.name;
                const nameBlock = adName
                    ? html`<div class="font-medium text-sm truncate">${adName}</div>
                           <div class="text-xs font-mono opacity-60 truncate">${ad.public_key.slice(0, 16)}...</div>`
                    : html`<div class="font-mono text-sm truncate">${ad.public_key.slice(0, 16)}...</div>`;
                let receiversBlock = nothing;
                if (ad.receivers && ad.receivers.length >= 1) {
                    receiversBlock = html`<div class="flex gap-0.5 justify-end mt-1">
                        ${ad.receivers.map(recv => {
                            const recvName = recv.tag_name || recv.name || truncateKey(recv.public_key, 12);
                            return html`<span class="text-sm" title=${recvName}>\u{1F4E1}</span>`;
                        })}
                    </div>`;
                } else if (ad.received_by) {
                    const recvTitle = ad.receiver_tag_name || ad.receiver_name || truncateKey(ad.received_by, 12);
                    receiversBlock = html`<span class="text-sm" title=${recvTitle}>\u{1F4E1}</span>`;
                }
                return html`<a href="/nodes/${ad.public_key}" class="card bg-base-100 shadow-sm block">
        <div class="card-body p-3">
            <div class="flex items-center justify-between gap-2">
                <div class="flex items-center gap-2 min-w-0">
                    <span class="text-lg flex-shrink-0" title=${ad.adv_type || 'Unknown'}>${emoji}</span>
                    <div class="min-w-0">
                        ${nameBlock}
                    </div>
                </div>
                <div class="text-right flex-shrink-0">
                    <div class="text-xs opacity-60">${formatDateTimeShort(ad.received_at)}</div>
                    ${receiversBlock}
                </div>
            </div>
        </div>
    </a>`;
            });

        const tableRows = advertisements.length === 0
            ? html`<tr><td colspan="3" class="text-center py-8 opacity-70">No advertisements found.</td></tr>`
            : advertisements.map(ad => {
                const emoji = typeEmoji(ad.adv_type);
                const adName = ad.node_tag_name || ad.node_name || ad.name;
                const nameBlock = adName
                    ? html`<div class="font-medium">${adName}</div>
                           <div class="text-xs font-mono opacity-70">${ad.public_key.slice(0, 16)}...</div>`
                    : html`<span class="font-mono text-sm">${ad.public_key.slice(0, 16)}...</span>`;
                let receiversBlock;
                if (ad.receivers && ad.receivers.length >= 1) {
                    receiversBlock = html`<div class="flex gap-1">
                        ${ad.receivers.map(recv => {
                            const recvName = recv.tag_name || recv.name || truncateKey(recv.public_key, 12);
                            return html`<a href="/nodes/${recv.public_key}" class="text-lg hover:opacity-70" title=${recvName}>\u{1F4E1}</a>`;
                        })}
                    </div>`;
                } else if (ad.received_by) {
                    const recvTitle = ad.receiver_tag_name || ad.receiver_name || truncateKey(ad.received_by, 12);
                    receiversBlock = html`<a href="/nodes/${ad.received_by}" class="text-lg hover:opacity-70" title=${recvTitle}>\u{1F4E1}</a>`;
                } else {
                    receiversBlock = html`<span class="opacity-50">-</span>`;
                }
                return html`<tr class="hover">
                <td>
                    <a href="/nodes/${ad.public_key}" class="link link-hover flex items-center gap-2">
                        <span class="text-lg" title=${ad.adv_type || 'Unknown'}>${emoji}</span>
                        <div>
                            ${nameBlock}
                        </div>
                    </a>
                </td>
                <td class="text-sm whitespace-nowrap">${formatDateTime(ad.received_at)}</td>
                <td>${receiversBlock}</td>
            </tr>`;
            });

        const paginationBlock = pagination(page, totalPages, '/advertisements', {
            search, public_key, member_id, limit,
        });

        renderPage(html`
<div class="card shadow mb-6 panel-solid" style="--panel-color: var(--color-neutral)">
    <div class="card-body py-4">
        <form method="GET" action="/advertisements" class="flex gap-4 flex-wrap items-end" @submit=${createFilterHandler('/advertisements', navigate)}>
            <div class="form-control">
                <label class="label py-1">
                    <span class="label-text">Search</span>
                </label>
                <input type="text" name="search" .value=${search} placeholder="Search by name, ID, or public key..." class="input input-bordered input-sm w-80" @keydown=${submitOnEnter} />
            </div>
            ${nodesFilter}
            ${membersFilter}
            <div class="flex gap-2 w-full sm:w-auto">
                <button type="submit" class="btn btn-primary btn-sm">Filter</button>
                <a href="/advertisements" class="btn btn-ghost btn-sm">Clear</a>
            </div>
        </form>
    </div>
</div>

<div class="lg:hidden space-y-3">
    ${mobileCards}
</div>

<div class="hidden lg:block overflow-x-auto overflow-y-visible bg-base-100 rounded-box shadow">
    <table class="table table-zebra">
        <thead>
            <tr>
                <th>Node</th>
                <th>Time</th>
                <th>Receivers</th>
            </tr>
        </thead>
        <tbody>
            ${tableRows}
        </tbody>
    </table>
 </div>

${paginationBlock}`, { total });
    }

    // Render page header immediately (old content stays visible until data loads)
    renderPage(nothing);

    let cleanup = null;
    try {
        const [data, nodesData, membersData] = await Promise.all([
            apiGet('/api/v1/advertisements', { limit, offset, search, public_key, member_id }),
            apiGet('/api/v1/nodes', { limit: 500 }),
            apiGet('/api/v1/members', { limit: 100 }),
        ]);

        advertisements = data.items || [];
        total = data.total || 0;
        const allNodes = nodesData.items || [];
        members = membersData.items || [];

        sortedNodes = allNodes.map(n => {
            const tagName = n.tags?.find(t => t.key === 'name')?.value;
            return { ...n, _sortName: (tagName || n.name || '').toLowerCase(), _displayName: tagName || n.name || n.public_key.slice(0, 12) + '...' };
        }).sort((a, b) => a._sortName.localeCompare(b._sortName));

        renderContent();
        startWebSocket();
        cleanup = () => {
            closed = true;
            if (socket) socket.close();
        };
    } catch (e) {
        renderPage(errorAlert(e.message));
    }
    return cleanup;
}
