/**
 * IGN WFS Integration Module - Compatibility Wrapper
 * This file now imports from the refactored modules for backward compatibility
 */

// Import the refactored client
import ignWFSClient, { IGNWFSClient } from './ign-wfs-client-refactored.js';

// Re-export everything for backward compatibility
export { IGNWFSClient };
export default ignWFSClient;

// Also make available on window for legacy code
if (typeof window !== 'undefined') {
    window.IGNWFSClient = IGNWFSClient;
    window.ignWFSClient = ignWFSClient;
}