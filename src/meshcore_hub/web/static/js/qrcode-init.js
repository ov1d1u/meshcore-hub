/**
 * MeshCore Hub - QR Code Generation
 *
 * Generates QR codes for adding MeshCore contacts.
 * Requires qrcodejs library to be loaded before this script.
 *
 * Configuration via window.qrCodeConfig:
 * - name: Contact name (required)
 * - publicKey: 64-char hex public key (required)
 * - advType: Node advertisement type (optional)
 * - containerId: ID of container element (default: 'qr-code')
 */

(function() {
    'use strict';

    // Get configuration
    var config = window.qrCodeConfig;
    if (!config || !config.publicKey) {
        console.warn('QR code config missing or invalid');
        return;
    }

    var nodeName = config.name || 'Node';
    var publicKey = config.publicKey;
    var advType = config.advType || '';
    var containerId = config.containerId || 'qr-code';

    // Map adv_type to numeric type for meshcore:// protocol
    var typeMap = {
        'chat': 1,
        'repeater': 2,
        'room': 3,
        'sensor': 4
    };
    var typeNum = typeMap[advType.toLowerCase()] || 1;

    // Build meshcore:// URL
    var meshcoreUrl = 'meshcore://contact/add?name=' + encodeURIComponent(nodeName) +
        '&public_key=' + publicKey +
        '&type=' + typeNum;

    // Generate QR code
    var qrContainer = document.getElementById(containerId);
    if (qrContainer && typeof QRCode !== 'undefined') {
        try {
            new QRCode(qrContainer, {
                text: meshcoreUrl,
                width: 256,
                height: 256,
                colorDark: '#000000',
                colorLight: '#ffffff',
                correctLevel: QRCode.CorrectLevel.L
            });
        } catch (error) {
            console.error('QR code generation failed:', error);
            qrContainer.innerHTML = '<p class="text-sm opacity-50">QR code unavailable</p>';
        }
    }
})();
