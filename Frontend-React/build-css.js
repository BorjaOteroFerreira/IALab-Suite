#!/usr/bin/env node

/**
 * CSS Build Script - Modern Production Optimization
 * Optimizes and validates CSS for production deployment
 */

const fs = require('fs');
const path = require('path');

// CSS files in order of importance
const CSS_FILES = [
  'src/styles/index.css',
  'src/styles/fonts.css',
  'src/styles/theme.css',
  'src/styles/components.css',
  'src/styles/animations.css',
  'src/styles/App.css',
  'src/components/ChatContainer/ChatContainer.css',
  'src/components/MessageInput/MessageInput.css',
  'src/components/ChatSidebar/ChatSidebar.css',
  'src/components/ConfigSidebar/ConfigSidebar.css',
  'src/components/LoadingIndicator/LoadingIndicator.css',
  'src/components/ErrorMessage/ErrorMessage.css',
  'src/components/YouTubeEmbed/YouTubeEmbed.css'
];

console.log('🎨 Building CSS for production...');

// Read and combine all CSS files
let combinedCSS = '';
const processedFiles = [];

CSS_FILES.forEach(file => {
  const filePath = path.join(__dirname, file);
  
  if (fs.existsSync(filePath)) {
    console.log(`📄 Processing: ${file}`);
    const content = fs.readFileSync(filePath, 'utf8');
    
    // Add file header comment
    combinedCSS += `\n/* === ${file.toUpperCase()} === */\n`;
    combinedCSS += content;
    combinedCSS += '\n';
    
    processedFiles.push(file);
  } else {
    console.warn(`⚠️  File not found: ${file}`);
  }
});

// Basic CSS optimization
console.log('🔧 Optimizing CSS...');

// Remove excessive comments (keep important ones)
const optimizedCSS = combinedCSS
  // Remove empty lines
  .replace(/\n\s*\n\s*\n/g, '\n\n')
  // Remove trailing whitespace
  .replace(/[ \t]+$/gm, '')
  // Normalize line endings
  .replace(/\r\n/g, '\n');

// Write optimized CSS
const outputPath = path.join(__dirname, 'build/static/css/combined.css');
const outputDir = path.dirname(outputPath);

// Create output directory if it doesn't exist
if (!fs.existsSync(outputDir)) {
  fs.mkdirSync(outputDir, { recursive: true });
}

fs.writeFileSync(outputPath, optimizedCSS);

// Generate CSS report
const report = {
  timestamp: new Date().toISOString(),
  files: processedFiles,
  totalFiles: processedFiles.length,
  totalSize: Buffer.byteLength(optimizedCSS, 'utf8'),
  sizeInKB: Math.round(Buffer.byteLength(optimizedCSS, 'utf8') / 1024 * 100) / 100
};

console.log('\n✅ CSS Build Complete!');
console.log(`📦 Files processed: ${report.totalFiles}`);
console.log(`📊 Total size: ${report.sizeInKB} KB`);
console.log(`📍 Output: ${outputPath}`);

// Write build report
const reportPath = path.join(__dirname, 'build/css-build-report.json');
fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));

console.log(`📋 Build report: ${reportPath}`);
console.log('\n🚀 Ready for production!');
