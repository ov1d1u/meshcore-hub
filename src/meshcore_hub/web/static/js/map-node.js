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
 * - elementId: Map container element ID (default: 'node-map')
 * - interactive: Enable map interactions (default: true)
 * - zoom: Initial zoom level (default: 15)
 * - showMarker: Show node marker (default: true)
 * - offsetX: Horizontal position of node (0-1, default: 0.5 = center)
 * - offsetY: Vertical position of node (0-1, default: 0.5 = center)
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
    var elementId = config.elementId || 'node-map';
    var interactive = config.interactive !== false; // Default true
    var zoomLevel = config.zoom || 15;
    var showMarker = config.showMarker !== false; // Default true
    var offsetX = typeof config.offsetX === 'number' ? config.offsetX : 0.5; // 0-1, default center
    var offsetY = typeof config.offsetY === 'number' ? config.offsetY : 0.5; // 0-1, default center

    // Check if map container exists
    var mapContainer = document.getElementById(elementId);
    if (!mapContainer) {
        return;
    }

    // Build map options
    var mapOptions = {};

    // Disable interactions if non-interactive
    if (!interactive) {
        mapOptions.dragging = false;
        mapOptions.touchZoom = false;
        mapOptions.scrollWheelZoom = false;
        mapOptions.doubleClickZoom = false;
        mapOptions.boxZoom = false;
        mapOptions.keyboard = false;
        mapOptions.zoomControl = false;
        mapOptions.attributionControl = false;
    }

    // Initialize map centered on the node's location
    var map = L.map(elementId, mapOptions).setView([nodeLat, nodeLon], zoomLevel);

    // Apply offset to position node at specified location instead of center
    // offsetX/Y of 0.5 = center (no pan), 0.33 = 1/3 from left/top
    if (offsetX !== 0.5 || offsetY !== 0.5) {
        var containerWidth = mapContainer.offsetWidth;
        var containerHeight = mapContainer.offsetHeight;
        // Pan amount: how far to move the map so node appears at offset position
        // Positive X = pan right (node moves left), Positive Y = pan down (node moves up)
        var panX = (0.5 - offsetX) * containerWidth;
        var panY = (0.5 - offsetY) * containerHeight;
        map.panBy([panX, panY], { animate: false });
    }

    // Add tile layer
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
    }).addTo(map);

    // Only add marker if showMarker is true
    if (showMarker) {
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

        // Only add popup if map is interactive
        if (interactive) {
            var typeHtml = nodeType ? '<p><span class="opacity-70">Type:</span> ' + nodeType + '</p>' : '';
            var popupContent = '<div class="p-2">' +
                '<h3 class="font-bold text-lg mb-2">' + emoji + ' ' + nodeName + '</h3>' +
                '<div class="space-y-1 text-sm">' +
                    typeHtml +
                    '<p><span class="opacity-70">Coordinates:</span> ' + nodeLat.toFixed(4) + ', ' + nodeLon.toFixed(4) + '</p>' +
                '</div>' +
            '</div>';
            marker.bindPopup(popupContent);
        }
    }
})();
