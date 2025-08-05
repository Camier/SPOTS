#!/usr/bin/env node
/**
 * Generate validation status badge for README
 */

import fs from 'fs/promises';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

async function generateBadge() {
    try {
        // Read latest validation report
        const reportPath = join(__dirname, 'validation-report.json');
        const report = JSON.parse(await fs.readFile(reportPath, 'utf8'));
        
        const { passed, total } = report.summary;
        const percentage = Math.round((passed / total) * 100);
        
        // Determine badge color
        let color;
        if (percentage === 100) {
            color = 'brightgreen';
        } else if (percentage >= 80) {
            color = 'green';
        } else if (percentage >= 60) {
            color = 'yellow';
        } else if (percentage >= 40) {
            color = 'orange';
        } else {
            color = 'red';
        }
        
        // Create badge markdown
        const badgeUrl = `https://img.shields.io/badge/Map%20Validation-${passed}%2F${total}%20(${percentage}%25)-${color}`;
        const badgeMarkdown = `![Map Validation](${badgeUrl})`;
        
        // Update README with badge
        const readmePath = join(dirname(__dirname), 'README.md');
        let readme = await fs.readFile(readmePath, 'utf8');
        
        // Replace existing badge or add at top
        const badgeRegex = /!\[Map Validation\]\(https:\/\/img\.shields\.io\/badge\/.*?\)/;
        if (badgeRegex.test(readme)) {
            readme = readme.replace(badgeRegex, badgeMarkdown);
        } else {
            // Add after main title
            readme = readme.replace(/^(# .*\n)/, `$1\n${badgeMarkdown}\n`);
        }
        
        await fs.writeFile(readmePath, readme);
        
        console.log(`✅ Badge updated: ${percentage}% (${passed}/${total})`);
        
        // Also save badge URL for CI
        await fs.writeFile(
            join(__dirname, 'badge.json'),
            JSON.stringify({ url: badgeUrl, markdown: badgeMarkdown }, null, 2)
        );
        
    } catch (error) {
        console.error('❌ Failed to generate badge:', error.message);
        process.exit(1);
    }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
    generateBadge();
}

export { generateBadge };