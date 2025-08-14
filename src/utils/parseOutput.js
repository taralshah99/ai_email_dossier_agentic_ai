/**
 * Parse CrewAI output and convert it to formatted HTML/markdown
 * Similar to the parse_crewai_output function in the Streamlit app
 */

export function parseCrewAIOutput(text) {
  if (!text) return '';
  
  // Convert the text to a string if it's not already 
  const textStr = String(text);
  
  // Replace markdown-style headers with HTML
  let parsed = textStr
    // Convert **bold** to <strong>
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Convert *italic* to <em>
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Convert headers
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h2>$1</h2>')
    .replace(/^# (.*$)/gim, '<h1>$1</h1>')
    // Convert bullet points
    .replace(/^- (.*$)/gim, '<li>$1</li>')
    // Convert numbered lists
    .replace(/^\d+\. (.*$)/gim, '<li>$1</li>')
    // Convert line breaks
    .replace(/\n/g, '<br>')
    // Wrap lists in ul tags
    .replace(/(<li>.*<\/li>)/g, '<ul>$1</ul>');
  
  // Clean up multiple consecutive <br> tags
  parsed = parsed.replace(/<br><br><br>/g, '<br><br>');
  
  return parsed;
}

/**
 * Format analysis results for display
 */
export function formatAnalysisResults(analysis) {
  if (!analysis) return '';
  
  // If it's already formatted HTML, return as is
  if (analysis.includes('<strong>') || analysis.includes('<em>')) {
    return analysis;
  }
  
  return parseCrewAIOutput(analysis);
}

/**
 * Extract product information from analysis
 */
export function extractProductInfo(analysis) {
  if (!analysis) {
    return { 
      client_name: 'Unknown Client', 
      product_name: 'Unknown Product', 
      product_domain: 'general product' 
    };
  }
  
  const text = String(analysis);

  // Extract client name
  const clientNameMatch = text.match(/Client Name:\s*\**(.+?)\**\s*$/m);
  const clientName = clientNameMatch ? clientNameMatch[1].trim() : 'Unknown Client';
  
  // Extract product name
  const productNameMatch = text.match(/Product Name:\s*\**(.+?)\**\s*$/m);
  const productName = productNameMatch ? productNameMatch[1].trim() : 'Unknown Product';
  
  // Extract product domain
  const productDomainMatch = text.match(/Product Domain:\s*\**(.+?)\**\s*$/m);
  const productDomain = productDomainMatch ? productDomainMatch[1].trim() : 'general product';
  
  return {
    client_name: clientName,
    product_name: productName,
    product_domain: productDomain
  };
} 