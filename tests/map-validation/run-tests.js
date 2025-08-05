#!/usr/bin/env node

/**
 * Run all test scenarios
 */

import { runAllScenarios } from './test-scenarios.js';

const options = {
    headless: !process.argv.includes('--show'),
    screenshotDir: './screenshots',
    baseUrl: 'http://localhost:8085'
};

console.log('🗺️  SPOTS Map Validation - Running All Tests');
console.log('==========================================\n');

runAllScenarios(options)
    .then(results => {
        // Generate summary
        let totalPassed = 0;
        let totalFailed = 0;
        
        Object.values(results).forEach(result => {
            if (result.passed) totalPassed++;
            else totalFailed++;
        });
        
        console.log('\n📊 Overall Summary:');
        console.log(`Total Scenarios: ${Object.keys(results).length}`);
        console.log(`Passed: ${totalPassed} ✅`);
        console.log(`Failed: ${totalFailed} ❌`);
        
        // Save results
        require('fs').writeFileSync(
            './validation-report-full.json',
            JSON.stringify(results, null, 2)
        );
        
        console.log('\nFull report saved to validation-report-full.json');
        
        process.exit(totalFailed > 0 ? 1 : 0);
    })
    .catch(error => {
        console.error('❌ Validation failed:', error.message);
        process.exit(1);
    });