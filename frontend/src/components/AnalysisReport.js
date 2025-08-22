import React, { useState } from 'react';
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
  
  h1, h2, h3 {
    color: var(--gray-800);
    margin: var(--space-5) 0 var(--space-3) 0;
    font-weight: 600;
  }
  
  h1 { font-size: 1.25rem; }
  h2 { font-size: 1.125rem; }
  h3 { font-size: 1rem; }
  
  strong {
    color: var(--gray-800);
    font-weight: 600;
  }
  
  em { 
    font-style: italic;
    color: var(--gray-700);
  }
  
  ul {
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
`;

const Section = styled.div`
  margin-bottom: var(--space-6);
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionTitle = styled.h3`
  font-size: 1.125rem;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 var(--space-4) 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  
  &::before {
    content: '';
    width: 3px;
    height: 18px;
    background: var(--primary-400);
    border-radius: 2px;
  }
`;



function AnalysisReport({ 
  structuredAnalysis, 
  rawAnalysis, 
  threadMetadata, 
  combinedMetadata, 
  productName, 
  productDomain 
}) {
  const hasStructured = structuredAnalysis && typeof structuredAnalysis === 'object';
  if (!hasStructured && !rawAnalysis) return null;

  // Get client name from structured analysis
  const clientName = structuredAnalysis?.client_name || 'Unknown Client';
  
  // Get product information with conditional display logic
  const getProductDisplay = () => {
    const hasProductName = productName && 
                          productName !== 'Unknown Product' && 
                          productName.toLowerCase() !== 'unknown';
    const hasProductDomain = productDomain && 
                            productDomain !== 'general product' &&
                            productDomain.toLowerCase() !== 'unknown';
    
    if (hasProductName && hasProductDomain) {
      return `${productName} (${productDomain})`;
    } else if (hasProductName) {
      return productName;
    } else if (hasProductDomain) {
      return productDomain;
    }
    return null;
  };
  
  // Get thread summary information
  const getThreadSummary = () => {
    // Use combined metadata for multiple threads, thread metadata for single thread
    const metadata = combinedMetadata || threadMetadata;
    if (!metadata) return null;
    
    // Calculate email count
    let emailCount = 0;
    if (combinedMetadata) {
      // For multiple threads, sum up message_count from all threads
      if (combinedMetadata.threads && Array.isArray(combinedMetadata.threads)) {
        emailCount = combinedMetadata.threads.reduce((total, thread) => {
          return total + (thread.message_count || 0);
        }, 0);
      }
    } else if (threadMetadata) {
      // For single thread, use message_count directly
      emailCount = threadMetadata.message_count || 0;
    }
    
    return {
      firstEmailDate: metadata.first_email_date,
      lastEmailDate: metadata.last_email_date,
      emailCount: emailCount,
      threadCount: metadata.thread_count || 1,
      participants: metadata.participants || {},
      totalParticipants: metadata.total_participants || Object.keys(metadata.participants || {}).length
    };
  };
  
  // Get consolidated email summaries as bullet points
  const getConsolidatedSummaries = () => {
    if (!hasStructured) return [];
    
    let allSummaries = [];
    
    // Check for groups first (newer format)
    if (Array.isArray(structuredAnalysis.groups) && structuredAnalysis.groups.length > 0) {
      structuredAnalysis.groups.forEach(group => {
        if (Array.isArray(group.email_summaries)) {
          allSummaries.push(...group.email_summaries);
        }
      });
    } else if (Array.isArray(structuredAnalysis.email_summaries)) {
      // Fallback to legacy format
      allSummaries = [...structuredAnalysis.email_summaries];
    }
    
    // Replace "Unknown Sender" with actual participant names
    const threadSummary = getThreadSummary();
    if (threadSummary && threadSummary.participants) {
      allSummaries = allSummaries.map(summary => {
        let updatedSummary = summary;
        
        // Look for "Unknown Sender" patterns and try to replace with actual names
        if (updatedSummary.toLowerCase().includes('unknown sender')) {
          // Try to find email patterns in the summary and match with participants
          const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
          const emailsInSummary = updatedSummary.match(emailRegex) || [];
          
          emailsInSummary.forEach(email => {
            const participant = threadSummary.participants[email.toLowerCase()];
            if (participant && participant.display_name) {
              // Replace "Unknown Sender" with the actual name when the email is mentioned
              updatedSummary = updatedSummary.replace(/unknown sender/gi, participant.display_name);
            }
          });
          
          // If no email found in summary but we have participants, try to replace with first participant
          if (!emailsInSummary.length && Object.keys(threadSummary.participants).length > 0) {
            const firstParticipant = Object.values(threadSummary.participants)[0];
            if (firstParticipant && firstParticipant.display_name) {
              updatedSummary = updatedSummary.replace(/unknown sender/gi, firstParticipant.display_name);
            }
          }
        }
        
        return updatedSummary;
      });
    }
    
    return allSummaries;
  };

  const threadSummary = getThreadSummary();
  const productDisplay = getProductDisplay();
  const consolidatedSummaries = getConsolidatedSummaries();

  return (
    <ReportContainer>
      <ReportTitle>Till date Agenda</ReportTitle>
      <ReportContent>
        {hasStructured ? (
          <>
            {/* Client Name */}
            <Section>
              <SectionTitle>Client Name</SectionTitle>
              <p>{clientName}</p>
            </Section>

            {/* Product Name and Domain */}
            {productDisplay && (
              <Section>
                <SectionTitle>Product Name and Domain</SectionTitle>
                <p>{productDisplay}</p>
              </Section>
            )}

            {/* Participants */}
            <Section>
              <SectionTitle>Participants</SectionTitle>
              {threadSummary && Object.keys(threadSummary.participants).length > 0 ? (
                <ul>
                  {Object.entries(threadSummary.participants).map(([email, participant]) => (
                    <li key={email}>
                      {participant.display_name || email} - {email}
                    </li>
                  ))}
                </ul>
              ) : (
                <p><em>No participant information available.</em></p>
              )}
            </Section>

            {/* Timeline Information */}
            <Section>
              <SectionTitle>Timeline Information</SectionTitle>
              {threadSummary ? (
                <div>
                  <p><strong>First Email:</strong> {threadSummary.firstEmailDate || 'Not available'}</p>
                  <p><strong>Last Email:</strong> {threadSummary.lastEmailDate || 'Not available'}</p>
                  <p><strong>Email Count:</strong> {threadSummary.emailCount}</p>
                  <p><strong>Thread Count:</strong> {threadSummary.threadCount}</p>
                  <p><strong>Total Participants:</strong> {threadSummary.totalParticipants}</p>
                </div>
              ) : (
                <p><em>Timeline information not available.</em></p>
              )}
            </Section>

            {/* Mail Thread Summary */}
            <Section>
              <SectionTitle>Mail Thread Summary</SectionTitle>
              {consolidatedSummaries.length > 0 ? (
                <ul>
                  {consolidatedSummaries.map((summary, idx) => (
                    <li key={`summary-${idx}`}>{summary}</li>
                  ))}
                </ul>
              ) : (
                <p><em>Thread summary information not available.</em></p>
              )}
            </Section>
          </>
        ) : (
          <div dangerouslySetInnerHTML={{ __html: rawAnalysis }} />
        )}
      </ReportContent>
    </ReportContainer>
  );
}

export default AnalysisReport;
