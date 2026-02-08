/**
 * MeshCore Hub - Node Detail Map
 *
 * Simple map for displaying a single node's location.
 * Requires Leaflet.js to be loaded before this script.
 *
 * Configuration via window.nodeMapConfig:
 * - lat: Node latitude (required)
 * - lon: Node longitude (required)
 * - name: Node display name (required)
 * - type: Node adv_type (optional)
 * - publicKey: Node public key (optional, for linking)
 */

(function() {
    'use strict';

    // Get configuration
    var config = window.nodeMapConfig;
    if (!config || typeof config.lat === 'undefined' || typeof config.lon === 'undefined') {
        console.warn('Node map config missing or invalid');
        return;
    }

    var nodeLat = config.lat;
    var nodeLon = config.lon;
    var nodeName = config.name || 'Unnamed Node';
    var nodeType = config.type || '';

    // Check if map container exists
    var mapContainer = document.getElementById('node-map');
    if (!mapContainer) {
        return;
    }

    // Initialize map centered on the node's location
    var map = L.map('node-map').setView([nodeLat, nodeLon], 15);

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    /**
     * Get emoji marker based on node type
     */
    function getNodeEmoji(type) {
        var normalizedType = type ? type.toLowerCase() : null;
        if (normalizedType === 'chat') return '💬';
        if (normalizedType === 'repeater') return '📡';
        if (normalizedType === 'room') return '🪧';
        return '📍';
    }

    // Create marker icon (just the emoji, no label)
    var emoji = getNodeEmoji(nodeType);
    var icon = L.divIcon({
        className: 'custom-div-icon',
        html: '<span style="font-size: 32px; text-shadow: 0 0 3px #1a237e, 0 0 6px #1a237e, 0 1px 2px rgba(0,0,0,0.7);">' + emoji + '</span>',
        iconSize: [32, 32],
        iconAnchor: [16, 16]
    });

    // Add marker
    var marker = L.marker([nodeLat, nodeLon], { icon: icon }).addTo(map);

    // Build popup content
    var typeHtml = nodeType ? '<p><span class="opacity-70">Type:</span> ' + nodeType + '</p>' : '';
    var popupContent = '<div class="p-2">' +
        '<h3 class="font-bold text-lg mb-2">' + emoji + ' ' + nodeName + '</h3>' +
        '<div class="space-y-1 text-sm">' +
            typeHtml +
            '<p><span class="opacity-70">Coordinates:</span> ' + nodeLat.toFixed(4) + ', ' + nodeLon.toFixed(4) + '</p>' +
        '</div>' +
    '</div>';

    // Add popup (shown on click, not by default)
    marker.bindPopup(popupContent);
})();
