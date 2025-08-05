#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const E2E_TEST_DIR = path.join(__dirname, '../tests/e2e');

async function convertTestFile(filePath) {
    console.log(`Converting ${path.basename(filePath)}...`);
    
    let content = await fs.readFile(filePath, 'utf-8');
    
    // Replace require statements with imports
    content = content.replace(/const puppeteer = require\('puppeteer'\);/g, 
        "import puppeteer from 'puppeteer';");
    content = content.replace(/const { expect } = require\('chai'\);/g, 
        "import { expect } from 'chai';");
    content = content.replace(/const path = require\('path'\);/g, 
        "import path from 'node:path';");
    content = content.replace(/const axe = require\('axe-core'\);/g, 
        "import axe from 'axe-core';");
    
    // Add ESM boilerplate and vitest imports
    if (!content.includes('import.meta.url')) {
        const esmBoilerplate = `import { fileURLToPath } from 'node:url';
import { describe, it, beforeAll, afterAll, beforeEach, afterEach } from 'vitest';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

`;
        // Insert after other imports
        const lastImportIndex = content.lastIndexOf("import");
        if (lastImportIndex !== -1) {
            const endOfLastImport = content.indexOf('\n', lastImportIndex) + 1;
            content = content.slice(0, endOfLastImport) + '\n' + esmBoilerplate + content.slice(endOfLastImport);
        }
    }
    
    // Replace before/after with beforeAll/afterAll
    content = content.replace(/\bbefore\s*\(/g, 'beforeAll(');
    content = content.replace(/\bafter\s*\(/g, 'afterAll(');
    
    await fs.writeFile(filePath, content, 'utf-8');
    console.log(`✓ Converted ${path.basename(filePath)}`);
}

async function main() {
    try {
        const files = await fs.readdir(E2E_TEST_DIR);
        const testFiles = files.filter(file => file.endsWith('.test.js'));
        
        console.log(`Found ${testFiles.length} test files to convert\n`);
        
        for (const file of testFiles) {
            if (file === 'accessibility.test.js') {
                console.log(`✓ Skipping ${file} (already converted)`);
                continue;
            }
            await convertTestFile(path.join(E2E_TEST_DIR, file));
        }
        
        console.log('\n✅ All test files converted to ESM format!');
    } catch (error) {
        console.error('Error converting tests:', error);
        process.exit(1);
    }
}

main();