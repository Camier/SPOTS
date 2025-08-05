#!/usr/bin/env node
/**
 * Run Map Validation Tests
 * Usage: node run-validation.js [scenario] [--headless] [--screenshots]
 */

import { runAllScenarios } from './test-scenarios.js';
import MapValidator from './map-validator.js';
import fs from 'fs/promises';

async function main() {
    const args = process.argv.slice(2);
    const scenario = args.find(arg => !arg.startsWith('--'));
    const headless = args.includes('--headless');
    const screenshots = args.includes('--screenshots');
    const showBrowser = args.includes('--show');
    
    console.log(`
🗺️  SPOTS Map Validation Tool
============================
    `);
    
    const options = {
        headless: showBrowser ? false : headless,
        slowMo: showBrowser ? 50 : 0,
        devtools: args.includes('--devtools'),
        screenshotDir: screenshots ? `./screenshots/${new Date().toISOString().split('T')[0]}` : './screenshots'
    };
    
    if (scenario) {
        // Run single scenario
        console.log(`Running scenario: ${scenario}\n`);
        
        const { testScenarios } = await import('./test-scenarios.js');
        const scenarioConfig = testScenarios[scenario];
        
        if (!scenarioConfig) {
            console.error(`❌ Unknown scenario: ${scenario}`);
            console.log('\nAvailable scenarios:');
            Object.keys(testScenarios).forEach(key => {
                console.log(`  - ${key}: ${testScenarios[key].name}`);
            });
            process.exit(1);
        }
        
        const validator = new MapValidator(options);
        await validator.init();
        
        try {
            await validator.runAllValidations(scenarioConfig.path);
        } catch (error) {
            console.error('❌ Validation failed:', error.message);
        } finally {
            await validator.close();
        }
    } else {
        // Run all scenarios
        console.log('Running all test scenarios...\n');
        
        const results = await runAllScenarios(options);
        
        // Summary
        console.log('\n' + '='.repeat(60));
        console.log('📊 VALIDATION SUMMARY');
        console.log('='.repeat(60) + '\n');
        
        let totalPassed = 0;
        let totalFailed = 0;
        
        Object.entries(results).forEach(([key, result]) => {
            const status = result.passed ? '✅ PASSED' : '❌ FAILED';
            console.log(`${status} - ${result.scenario}`);
            
            if (result.tests) {
                const passed = result.tests.filter(t => t.passed).length;
                const total = result.tests.length;
                console.log(`         ${passed}/${total} tests passed`);
                
                totalPassed += passed;
                totalFailed += (total - passed);
            }
            
            if (result.error) {
                console.log(`         Error: ${result.error}`);
            }
        });
        
        console.log('\n' + '-'.repeat(60));
        console.log(`Total: ${totalPassed} passed, ${totalFailed} failed`);
        console.log('-'.repeat(60) + '\n');
        
        // Save report to JSON
        const report = {
            timestamp: new Date().toISOString(),
            summary: {
                total: totalPassed + totalFailed,
                passed: totalPassed,
                failed: totalFailed
            },
            scenarios: results
        };
        
        await fs.writeFile(
            './validation-report.json',
            JSON.stringify(report, null, 2)
        );
        
        console.log('📄 Report saved to validation-report.json');
        
        // Generate badge if all tests passed
        if (totalFailed === 0) {
            try {
                const { generateBadge } = await import('./generate-badge.js');
                await generateBadge();
            } catch (error) {
                console.log('⚠️  Could not generate badge:', error.message);
            }
        }
        
        // Exit with error code if any tests failed
        if (totalFailed > 0) {
            process.exit(1);
        }
    }
}

// Run with error handling
main().catch(error => {
    console.error('❌ Fatal error:', error);
    process.exit(1);
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    console.log('\n\n⚠️  Validation interrupted by user');
    process.exit(0);
});