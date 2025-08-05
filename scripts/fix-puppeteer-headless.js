#!/usr/bin/env node

import fs from 'fs/promises';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const E2E_TEST_DIR = path.join(__dirname, '../tests/e2e');

async function fixHeadlessMode(filePath) {
    let content = await fs.readFile(filePath, 'utf-8');
    
    // Replace headless: true with headless: "new"
    content = content.replace(/headless:\s*true/g, 'headless: "new"');
    
    await fs.writeFile(filePath, content, 'utf-8');
    console.log(`✓ Fixed headless mode in ${path.basename(filePath)}`);
}

async function main() {
    const files = await fs.readdir(E2E_TEST_DIR);
    const testFiles = files.filter(file => file.endsWith('.test.js'));
    
    for (const file of testFiles) {
        await fixHeadlessMode(path.join(E2E_TEST_DIR, file));
    }
    
    console.log('\n✅ Updated all tests to use new headless mode!');
}

main();