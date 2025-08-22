import React from 'react';
import styled, { keyframes } from 'styled-components';

const fadeInUp = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const ReportContainer = styled.div`
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-8);
  padding: var(--space-8);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-lg);
  animation: ${fadeInUp} 0.6s ease-out;
`;

const ReportTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gray-800);
  margin: 0 0 var(--space-6) 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  
  &::before {
    content: '';
    width: 4px;
    height: 24px;
    background: var(--primary-500);
    border-radius: 2px;
  }
`;

const ReportContent = styled.div`
  color: var(--gray-800);
  line-height: 1.6;
  
  h1, h2, h3, h4, h5, h6 {
    color: var(--gray-800);
    margin: var(--space-5) 0 var(--space-3) 0;
    font-weight: 600;
  }
  
  h1 { font-size: 1.5rem; }
  h2 { font-size: 1.25rem; }
  h3 { font-size: 1.125rem; }
  h4 { font-size: 1rem; }
  h5 { font-size: 0.875rem; }
  h6 { font-size: 0.75rem; }
  
  strong {
    color: var(--gray-800);
    font-weight: 600;
  }
  
  em { 
    font-style: italic;
    color: var(--gray-700);
  }
  
  ul, ol {
    margin: var(--space-3) 0;
    padding-left: var(--space-5);
  }
  
  li { 
    margin-bottom: var(--space-2);
    color: var(--gray-700);
  }
  
  p { 
    margin: var(--space-3) 0;
    color: var(--gray-700);
  }
  
  a {
    color: var(--primary-600);
    text-decoration: none;
    
    &:hover {
      text-decoration: underline;
    }
  }
  
  blockquote {
    margin: var(--space-4) 0;
    padding: var(--space-4);
    background: var(--gray-50);
    border-left: 4px solid var(--primary-400);
    border-radius: var(--radius-md);
    font-style: italic;
  }
  
  code {
    background: var(--gray-100);
    padding: 2px 6px;
    border-radius: var(--radius-sm);
    font-family: 'Monaco', 'Consolas', monospace;
    font-size: 0.875rem;
  }
  
  pre {
    background: var(--gray-100);
    padding: var(--space-4);
    border-radius: var(--radius-md);
    overflow-x: auto;
    margin: var(--space-4) 0;
    
    code {
      background: none;
      padding: 0;
    }
  }
  
  table {
    width: 100%;
    border-collapse: collapse;
    margin: var(--space-4) 0;
    
    th, td {
      border: 1px solid var(--gray-200);
      padding: var(--space-3);
      text-align: left;
    }
    
    th {
      background: var(--gray-50);
      font-weight: 600;
    }
  }
  
  hr {
    border: none;
    height: 1px;
    background: var(--gray-200);
    margin: var(--space-6) 0;
  }
`;

function ClientDossierReport({ clientDossierData }) {
  if (!clientDossierData || !clientDossierData.client_dossier) {
    return null;
  }

  // Convert markdown-like content to HTML for better rendering
  const processMarkdownContent = (content) => {
    return content
      // Convert headers
      .replace(/^### (.*$)/gim, '<h3>$1</h3>')
      .replace(/^## (.*$)/gim, '<h2>$1</h2>')
      .replace(/^# (.*$)/gim, '<h1>$1</h1>')
      // Convert bold text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      // Convert italic text
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      // Convert bullet points
      .replace(/^- (.*$)/gim, '<li>$1</li>')
      // Wrap consecutive list items in ul tags
      .replace(/(<li>.*<\/li>)/gs, (match) => {
        const items = match.split('</li>').filter(item => item.trim()).map(item => item + '</li>');
        return '<ul>' + items.join('') + '</ul>';
      })
      // Convert line breaks
      .replace(/\n/g, '<br>');
  };

  const processedContent = processMarkdownContent(clientDossierData.client_dossier);

  return (
    <ReportContainer>
      <ReportTitle>Client Dossier</ReportTitle>
      <ReportContent>
        <div dangerouslySetInnerHTML={{ __html: processedContent }} />
      </ReportContent>
    </ReportContainer>
  );
}

export default ClientDossierReport;
