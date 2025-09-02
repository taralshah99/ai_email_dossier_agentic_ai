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
  productDomain,
  relevancyAnalysis 
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
    
    // Debug: Log the metadata to see what we're working with
    console.log("[AnalysisReport] Debug - metadata:", metadata);
    console.log("[AnalysisReport] Debug - combinedMetadata:", combinedMetadata);
    console.log("[AnalysisReport] Debug - threadMetadata:", threadMetadata);
    
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
    
    const result = {
      firstEmailDate: metadata.first_email_date,
      lastEmailDate: metadata.last_email_date,
      emailCount: emailCount,
      threadCount: metadata.thread_count || 1,
      participants: metadata.participants || {},
      totalParticipants: metadata.total_participants || Object.keys(metadata.participants || {}).length
    };
    
    // Debug: Log the result
    console.log("[AnalysisReport] Debug - threadSummary result:", result);
    
    return result;
  };
  
  // Get consolidated email summaries as bullet points
  const getConsolidatedSummaries = () => {
    if (!hasStructured) return [];
    
    let allSummaries = [];
    
    // Debug: Log the structured analysis to see what we're working with
    console.log("[AnalysisReport] Debug - structuredAnalysis:", structuredAnalysis);
    console.log("[AnalysisReport] Debug - relevancyAnalysis:", relevancyAnalysis);
    
    // Check for relevant_groups first (new relevancy-aware format)
    if (relevancyAnalysis && Array.isArray(relevancyAnalysis.relevant_groups) && relevancyAnalysis.relevant_groups.length > 0) {
      console.log("[AnalysisReport] Using relevancyAnalysis.relevant_groups");
      relevancyAnalysis.relevant_groups.forEach(group => {
        if (Array.isArray(group.email_summaries)) {
          allSummaries.push(...group.email_summaries);
        }
      });
    } else if (Array.isArray(structuredAnalysis.relevant_groups) && structuredAnalysis.relevant_groups.length > 0) {
      console.log("[AnalysisReport] Using structuredAnalysis.relevant_groups");
      structuredAnalysis.relevant_groups.forEach(group => {
        if (Array.isArray(group.email_summaries)) {
          allSummaries.push(...group.email_summaries);
        }
      });
    } else if (Array.isArray(structuredAnalysis.groups) && structuredAnalysis.groups.length > 0) {
      console.log("[AnalysisReport] Using structuredAnalysis.groups");
      // Extract email summaries from groups format
      structuredAnalysis.groups.forEach(group => {
        if (Array.isArray(group.email_summaries)) {
          console.log(`[AnalysisReport] Found ${group.email_summaries.length} email summaries in group:`, group.email_summaries);
          allSummaries.push(...group.email_summaries);
        }
      });
    } else if (Array.isArray(structuredAnalysis.email_summaries)) {
      console.log("[AnalysisReport] Using structuredAnalysis.email_summaries");
      // Fallback to legacy format - This should work for single threads
      allSummaries = [...structuredAnalysis.email_summaries];
    }
    
    console.log("[AnalysisReport] Debug - allSummaries found:", allSummaries);
    
    // If no summaries found from AI analysis, don't create basic summaries
    // This prevents showing generic thread info instead of actual content
    if (allSummaries.length === 0) {
      console.log("[AnalysisReport] No AI summaries found - checking what's available:");
      console.log("- structuredAnalysis keys:", Object.keys(structuredAnalysis || {}));
      console.log("- relevancyAnalysis keys:", Object.keys(relevancyAnalysis || {}));
      // Return empty array instead of creating generic summaries
      return [];
    }
    
         // Replace "Unknown Sender" with actual participant names
     const threadSummary = getThreadSummary();
     if (threadSummary && threadSummary.participants) {
       allSummaries = allSummaries.map(summary => {
         let updatedSummary = summary;
         
         // Look for various "unknown sender" patterns and try to replace with actual names
         const unknownPatterns = [
           /unknown sender/gi,
           /unnamed sender/gi,
           /unidentified sender/gi,
           /anonymous sender/gi,
           /sender/gi
         ];
         
         // Try to find email patterns in the summary and match with participants
         const emailRegex = /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b/g;
         const emailsInSummary = updatedSummary.match(emailRegex) || [];
         
         // Replace unknown sender patterns with actual participant names
         unknownPatterns.forEach(pattern => {
           if (updatedSummary.toLowerCase().includes(pattern.source.replace(/[.*+?^${}()|[\]\\]/g, '\\$&').toLowerCase())) {
             // If we have emails in the summary, try to match with participants
             if (emailsInSummary.length > 0) {
               emailsInSummary.forEach(email => {
                 const participant = threadSummary.participants[email.toLowerCase()];
                 if (participant && participant.display_name) {
                   // Replace the pattern with the actual name when the email is mentioned
                   updatedSummary = updatedSummary.replace(pattern, participant.display_name);
                 }
               });
             } else {
               // If no email found in summary but we have participants, try to replace with first participant
               if (Object.keys(threadSummary.participants).length > 0) {
                 const firstParticipant = Object.values(threadSummary.participants)[0];
                 if (firstParticipant && firstParticipant.display_name) {
                   updatedSummary = updatedSummary.replace(pattern, firstParticipant.display_name);
                 }
               }
             }
           }
         });
         
         // Additional pattern matching for common generic terms
         const genericPatterns = [
           { pattern: /\b(?:the|an?)\s+(?:sender|person|user|participant)\b/gi, replacement: 'the sender' },
           { pattern: /\b(?:some|one|a)\s+(?:sender|person|user|participant)\b/gi, replacement: 'someone' },
           { pattern: /\b(?:email|message)\s+(?:sender|from|author)\b/gi, replacement: 'email sender' }
         ];
         
         genericPatterns.forEach(({ pattern, replacement }) => {
           if (updatedSummary.match(pattern)) {
             // Try to replace with actual participant names
             if (Object.keys(threadSummary.participants).length > 0) {
               const firstParticipant = Object.values(threadSummary.participants)[0];
               if (firstParticipant && firstParticipant.display_name) {
                 updatedSummary = updatedSummary.replace(pattern, firstParticipant.display_name);
               }
             }
           }
         });
         
         return updatedSummary;
       });
     }
    
    return allSummaries;
  };

  // Get thread agenda and discussion points
  const getThreadAgenda = () => {
    if (!hasStructured) return null;
    
    // Try to extract agenda from global summary or relevancy insights
    if (relevancyAnalysis && relevancyAnalysis.relevancy_insights) {
      return relevancyAnalysis.relevancy_insights;
    }
    
    if (structuredAnalysis.global_summary && structuredAnalysis.global_summary.agenda) {
      return structuredAnalysis.global_summary.agenda;
    }
    
    if (structuredAnalysis.global_summary && structuredAnalysis.global_summary.summary) {
      return structuredAnalysis.global_summary.summary;
    }
    
    // Try to extract from final_conclusion
    if (structuredAnalysis.final_conclusion) {
      return structuredAnalysis.final_conclusion;
    }
    
    // Try to get from conversation summary
    if (structuredAnalysis.conversation_summary) {
      return structuredAnalysis.conversation_summary;
    }
    
    return null;
  };

  // Get detailed thread information for better organization
  const getDetailedThreadInfo = () => {
    if (!combinedMetadata || !combinedMetadata.threads) return [];
    
    return combinedMetadata.threads.map((thread, index) => {
      const participants = thread.participants || {};
      const participantList = Object.entries(participants).map(([email, participant]) => 
        participant.display_name || email
      ).join(', ');
      
      // Create a more detailed participant list with emails
      const detailedParticipantList = Object.entries(participants).map(([email, participant]) => ({
        email: email,
        name: participant.display_name || email,
        displayText: participant.display_name ? `${participant.display_name} - ${email}` : email
      }));
      
      return {
        id: thread.thread_id || `thread-${index}`,
        subject: thread.subject || `Thread ${index + 1}`,
        messageCount: thread.message_count || 0,
        participants: participantList,
        detailedParticipants: detailedParticipantList,
        firstEmail: thread.first_email_date,
        lastEmail: thread.last_email_date,
        isRelevant: thread.is_relevant !== false // Default to true unless explicitly marked as irrelevant
      };
    });
  };

  // Get thread-specific summaries and agenda from AI analysis
  const getThreadSpecificData = (threadIndex) => {
    let threadSummary = null;
    let threadAgenda = null;
    
    // Try to find thread-specific data from structured analysis
    if (hasStructured) {
      // Look for summaries in relevant groups or email summaries
      if (relevancyAnalysis && Array.isArray(relevancyAnalysis.relevant_groups)) {
        relevancyAnalysis.relevant_groups.forEach(group => {
          if (group.email_summaries && group.email_summaries.length > threadIndex) {
            threadSummary = group.email_summaries[threadIndex];
          }
        });
      }
      
      // Fallback to structured analysis
      if (!threadSummary && Array.isArray(structuredAnalysis.email_summaries) && structuredAnalysis.email_summaries.length > threadIndex) {
        threadSummary = structuredAnalysis.email_summaries[threadIndex];
      }
      
      // Look for thread-specific agenda
      if (structuredAnalysis.global_summary && structuredAnalysis.global_summary.thread_agendas && structuredAnalysis.global_summary.thread_agendas[threadIndex]) {
        threadAgenda = structuredAnalysis.global_summary.thread_agendas[threadIndex];
      }
    }
    
    // If no specific summary found, create a basic one from thread metadata
    const threadInfo = detailedThreadInfo[threadIndex];
    if (!threadSummary && threadInfo) {
      threadSummary = `This thread contains ${threadInfo.messageCount} message${threadInfo.messageCount !== 1 ? 's' : ''} discussing "${threadInfo.subject}". The conversation took place between ${threadInfo.firstEmail ? new Date(threadInfo.firstEmail).toLocaleDateString() : 'unknown date'} and ${threadInfo.lastEmail ? new Date(threadInfo.lastEmail).toLocaleDateString() : 'unknown date'}.`;
    }
    
    if (!threadAgenda && threadInfo) {
      threadAgenda = `This thread focuses on "${threadInfo.subject}" with ${threadInfo.messageCount} message${threadInfo.messageCount !== 1 ? 's' : ''} exchanged between the participants. The discussion appears to be ${threadInfo.messageCount > 5 ? 'an extended conversation' : 'a brief exchange'} on this topic.`;
    }
    
    return { threadSummary, threadAgenda };
  };

  // Get relevant groups for display
  const getRelevantGroups = () => {
    if (relevancyAnalysis && Array.isArray(relevancyAnalysis.relevant_groups)) {
      return relevancyAnalysis.relevant_groups;
    }
    // Fallback to structuredAnalysis if relevancyAnalysis is not available
    if (!hasStructured || !Array.isArray(structuredAnalysis.relevant_groups)) {
      return [];
    }
    return structuredAnalysis.relevant_groups;
  };

  // Get irrelevant threads for display
  const getIrrelevantThreads = () => {
    let irrelevantThreads = [];
    
    console.log("[AnalysisReport] Debugging irrelevant threads extraction:");
    console.log("[AnalysisReport] relevancyAnalysis:", relevancyAnalysis);
    console.log("[AnalysisReport] structuredAnalysis:", structuredAnalysis);
    
    // First, try to get AI-processed irrelevant threads from structured analysis
    if (hasStructured && Array.isArray(structuredAnalysis.irrelevant_threads)) {
      irrelevantThreads = structuredAnalysis.irrelevant_threads;
      console.log("[AnalysisReport] Using AI-processed irrelevant threads from structuredAnalysis:", irrelevantThreads);
    } else if (relevancyAnalysis && Array.isArray(relevancyAnalysis.irrelevant_threads)) {
      // If no AI-processed content, use raw thread data and create fallback content
      console.log("[AnalysisReport] No AI-processed content, creating fallback from raw thread data");
      irrelevantThreads = relevancyAnalysis.irrelevant_threads.map((rawThread, index) => {
        // Create fallback content from raw thread data
        const threadSubject = rawThread.subject || `Thread ${index + 1}`;
        const messageCount = rawThread.message_count || 0;
        const participants = rawThread.participants || {};
        const participantNames = Object.values(participants).map(p => p.display_name || p.email).join(', ');
        
        return {
          thread_subject: threadSubject,
          summary: `This thread contains ${messageCount} messages discussing "${threadSubject}". The conversation involves ${Object.keys(participants).length} participants: ${participantNames}.`,
          reason_for_irrelevancy: `This thread focuses on "${threadSubject}" which is separate from other business discussions.`,
          email_summaries: rawThread.content_snippets ? rawThread.content_snippets.slice(0, 3).map((snippet, idx) => 
            `Email ${idx + 1}: ${snippet.substring(0, 100)}${snippet.length > 100 ? '...' : ''}`
          ) : [
            `Initial contact regarding ${threadSubject}`,
            `Follow-up discussion about ${threadSubject}`,
            `Final communication on ${threadSubject}`
          ],
          discussion_agenda: `Discussion focused on ${threadSubject} and related topics with ${messageCount} messages exchanged.`
        };
      });
      console.log("[AnalysisReport] Created fallback irrelevant threads:", irrelevantThreads);
    }
    
    // If no irrelevant threads found at all, create basic ones from combined metadata
    if (irrelevantThreads.length === 0 && combinedMetadata && combinedMetadata.threads) {
      console.log("[AnalysisReport] No irrelevant threads found, creating basic ones from combined metadata");
      irrelevantThreads = combinedMetadata.threads.map((thread, index) => ({
        thread_subject: thread.subject || `Thread ${index + 1}`,
        summary: `This thread contains ${thread.message_count || 0} messages discussing "${thread.subject || `Thread ${index + 1}`}".`,
        reason_for_irrelevancy: "Thread was analyzed separately due to low relevancy with other threads",
        email_summaries: [
          `Initial contact regarding ${thread.subject || `Thread ${index + 1}`}`,
          `Follow-up discussion about ${thread.subject || `Thread ${index + 1}`}`,
          `Final communication on ${thread.subject || `Thread ${index + 1}`}`
        ],
        discussion_agenda: `Discussion focused on ${thread.subject || `Thread ${index + 1}`} and related topics.`
      }));
    }
    
         // Debug: Log the structure of each irrelevant thread
     if (irrelevantThreads.length > 0) {
       console.log("[AnalysisReport] Irrelevant threads structure:");
       irrelevantThreads.forEach((thread, index) => {
         console.log(`[AnalysisReport] Thread ${index} full content:`, thread);
         console.log(`[AnalysisReport] Thread ${index} summary:`, thread.summary);
         console.log(`[AnalysisReport] Thread ${index} discussion_agenda:`, thread.discussion_agenda);
         console.log(`[AnalysisReport] Thread ${index} email_summaries:`, thread.email_summaries);
         console.log(`[AnalysisReport] Thread ${index} reason_for_irrelevancy:`, thread.reason_for_irrelevancy);
       });
     }
    
    return irrelevantThreads;
  };

  // Get relevancy insights
  const getRelevancyInsights = () => {
    if (relevancyAnalysis && relevancyAnalysis.relevancy_insights) {
      return relevancyAnalysis.relevancy_insights;
    }
    // Fallback to structuredAnalysis if relevancyAnalysis is not available
    if (!hasStructured || !structuredAnalysis.global_summary) {
      return null;
    }
    return structuredAnalysis.global_summary.relevancy_insights;
  };

  // Check if we should show the consolidated thread summary
  const shouldShowConsolidatedSummary = () => {
    // Show consolidated summary if we have summaries but no clear relevancy grouping
    const hasSummaries = consolidatedSummaries.length > 0;
    const hasRelevancyGroups = relevantGroups.length > 0;
    const hasIrrelevantThreads = irrelevantThreads.length > 0;
    
    // Show if we have summaries but no relevancy analysis, OR if we have summaries but no clear grouping
    return hasSummaries && (!relevancyAnalysis || (!hasRelevancyGroups && !hasIrrelevantThreads));
  };

  const threadSummary = getThreadSummary();
  const productDisplay = getProductDisplay();
  const consolidatedSummaries = getConsolidatedSummaries();
  const relevantGroups = getRelevantGroups();
  const irrelevantThreads = getIrrelevantThreads();
  const relevancyInsights = getRelevancyInsights();
  const showConsolidatedSummary = shouldShowConsolidatedSummary();
  const threadAgenda = getThreadAgenda();
  const detailedThreadInfo = getDetailedThreadInfo();

  return (
    <ReportContainer>
      <ReportTitle>Past Summary</ReportTitle>
      <ReportContent>
        {hasStructured ? (
          <>
            {/* Only show top-level summary sections if there are no irrelevant threads */}
            {irrelevantThreads.length <= 1 && (
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

                {/* Thread Agenda - What was discussed */}
                {threadAgenda && (
                  <Section>
                    <SectionTitle>Discussion Agenda</SectionTitle>
                    <div style={{ 
                      padding: 'var(--space-4)', 
                      backgroundColor: 'var(--blue-50)', 
                      borderRadius: 'var(--radius-lg)',
                      border: '1px solid var(--blue-200)'
                    }}>
                      <p style={{ margin: 0, color: 'var(--blue-800)', lineHeight: '1.6' }}>
                        {threadAgenda}
                      </p>
                    </div>
                  </Section>
                )}
              </>
            )}

            {/* Relevancy Insights */}
            {relevancyInsights && !threadAgenda && (
              <Section>
                <SectionTitle>Relevancy Analysis</SectionTitle>
                <p>{relevancyInsights}</p>
              </Section>
            )}

            {/* Mail Thread Summary - Show for single thread or when not showing individual thread analysis */}
            {consolidatedSummaries.length > 0 && irrelevantThreads.length <= 1 && (
              <Section>
                <SectionTitle>Mail Thread Summary</SectionTitle>
                <ul>
                  {consolidatedSummaries.map((summary, idx) => (
                    <li key={`summary-${idx}`} style={{ marginBottom: 'var(--space-2)' }}>{summary}</li>
                  ))}
                </ul>
              </Section>
            )}
            
            {/* Show message if no summaries available */}
            {consolidatedSummaries.length === 0 && irrelevantThreads.length <= 1 && (
              <Section>
                <SectionTitle>Mail Thread Summary</SectionTitle>
                <p style={{ color: 'var(--gray-500)', fontStyle: 'italic' }}>
                  Detailed email summaries are being processed. Please check the raw analysis or try refreshing the analysis.
                </p>
                {/* Debug info - remove this after fixing */}
                <div style={{ 
                  marginTop: 'var(--space-3)', 
                  padding: 'var(--space-3)', 
                  backgroundColor: 'var(--yellow-50)', 
                  borderRadius: 'var(--radius-md)',
                  border: '1px solid var(--yellow-200)',
                  fontSize: '0.8rem',
                  fontFamily: 'monospace'
                }}>
                  <strong>Debug Info:</strong><br/>
                  <strong>Available keys in structuredAnalysis:</strong> {Object.keys(structuredAnalysis || {}).join(', ')}<br/>
                  <strong>email_summaries type:</strong> {Array.isArray(structuredAnalysis?.email_summaries) ? 'array' : typeof structuredAnalysis?.email_summaries}<br/>
                  <strong>email_summaries length:</strong> {Array.isArray(structuredAnalysis?.email_summaries) ? structuredAnalysis.email_summaries.length : 'N/A'}<br/>
                  <strong>groups type:</strong> {Array.isArray(structuredAnalysis?.groups) ? 'array' : typeof structuredAnalysis?.groups}<br/>
                  <strong>groups length:</strong> {Array.isArray(structuredAnalysis?.groups) ? structuredAnalysis.groups.length : 'N/A'}<br/>
                  {structuredAnalysis?.groups && (
                    <>
                      <strong>groups content:</strong> {JSON.stringify(structuredAnalysis.groups, null, 2)}
                    </>
                  )}
                  {structuredAnalysis?.email_summaries && (
                    <>
                      <strong>email_summaries content:</strong> {JSON.stringify(structuredAnalysis.email_summaries, null, 2)}
                    </>
                  )}
                </div>
              </Section>
            )}

            {/* Individual Thread Analysis - Only for multiple irrelevant threads */}
            {irrelevantThreads.length > 1 && (
              <Section>
                <SectionTitle>Individual Thread Analysis</SectionTitle>
                <p style={{ fontSize: '0.9rem', color: 'var(--gray-600)', marginBottom: 'var(--space-4)' }}>
                  Each thread has been analyzed separately to provide clear, distinct summaries:
                </p>
                {irrelevantThreads.map((thread, threadIndex) => {
                  const threadInfo = detailedThreadInfo[threadIndex];
                  
                  return (
                    <div key={`irrelevant-${threadIndex}`} style={{ 
                      marginBottom: 'var(--space-8)', 
                      padding: 0,
                      backgroundColor: 'transparent'
                    }}>
                      {/* Thread Group Header - More Prominent */}
                      <div style={{
                        backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-600)`,
                        color: 'white',
                        padding: 'var(--space-4)', 
                        borderRadius: 'var(--radius-lg) var(--radius-lg) 0 0',
                        marginBottom: 0
                      }}>
                        <h3 style={{ 
                          margin: 0, 
                          fontSize: '1.3rem',
                          fontWeight: '700',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 'var(--space-2)'
                        }}>
                          <span style={{
                            backgroundColor: 'rgba(255,255,255,0.2)',
                            padding: 'var(--space-1) var(--space-2)',
                            borderRadius: 'var(--radius-md)',
                            fontSize: '0.9rem',
                            fontWeight: '600'
                          }}>
                            Thread {threadIndex + 1}
                          </span>
                          {thread.thread_subject || threadInfo?.subject || `Thread ${threadIndex + 1}`}
                        </h3>
                        {threadInfo && (
                          <p style={{ 
                            margin: 'var(--space-2) 0 0 0', 
                            fontSize: '0.9rem', 
                            opacity: 0.9,
                            fontWeight: '400'
                          }}>
                            {threadInfo.messageCount} message{threadInfo.messageCount !== 1 ? 's' : ''} • {threadInfo.detailedParticipants?.length || 0} participant{(threadInfo.detailedParticipants?.length || 0) !== 1 ? 's' : ''}
                          </p>
                        )}
                      </div>
                      
                      {/* Thread Past Summary Section */}
                      <div style={{ 
                        backgroundColor: 'white', 
                        borderRadius: '0 0 var(--radius-lg) var(--radius-lg)',
                        border: `2px solid var(--${threadIndex === 0 ? 'blue' : 'green'}-200)`,
                        borderTop: 'none',
                        overflow: 'hidden'
                      }}>
                        {/* Thread Content */}
                        <div style={{ padding: 'var(--space-6)' }}>
                          {/* Client Name */}
                          <div style={{ marginBottom: 'var(--space-5)' }}>
                            <h5 style={{ 
                              color: 'var(--gray-800)', 
                              marginBottom: 'var(--space-2)', 
                              fontSize: '1.1rem',
                              fontWeight: '600',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 'var(--space-2)'
                            }}>
                              <span style={{ 
                                width: '4px', 
                                height: '16px', 
                                backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-500)`,
                                borderRadius: '2px'
                              }}></span>
                              Client Name
                            </h5>
                            <p style={{ margin: 0, color: 'var(--gray-700)', fontSize: '1rem', fontWeight: '500' }}>
                              {clientName}
                            </p>
                          </div>

                          {/* Product Name and Domain */}
                          {productDisplay && (
                            <div style={{ marginBottom: 'var(--space-5)' }}>
                              <h5 style={{ 
                                color: 'var(--gray-800)', 
                                marginBottom: 'var(--space-2)', 
                                fontSize: '1.1rem',
                                fontWeight: '600',
                                display: 'flex',
                                alignItems: 'center',
                                gap: 'var(--space-2)'
                              }}>
                                <span style={{ 
                                  width: '4px', 
                                  height: '16px', 
                                  backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-500)`,
                                  borderRadius: '2px'
                                }}></span>
                                Product Name and Domain
                              </h5>
                              <p style={{ margin: 0, color: 'var(--gray-700)', fontSize: '1rem', fontWeight: '500' }}>
                                {productDisplay}
                              </p>
                            </div>
                          )}

                          {/* Thread Participants */}
                          <div style={{ marginBottom: 'var(--space-5)' }}>
                            <h5 style={{ 
                              color: 'var(--gray-800)', 
                              marginBottom: 'var(--space-2)', 
                              fontSize: '1.1rem',
                              fontWeight: '600',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 'var(--space-2)'
                            }}>
                              <span style={{ 
                                width: '4px', 
                                height: '16px', 
                                backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-500)`,
                                borderRadius: '2px'
                              }}></span>
                              Participants
                            </h5>
                            {threadInfo && threadInfo.detailedParticipants && threadInfo.detailedParticipants.length > 0 ? (
                              <ul style={{ margin: 0, paddingLeft: 'var(--space-4)', color: 'var(--gray-700)' }}>
                                {threadInfo.detailedParticipants.map((participant, idx) => (
                                  <li key={idx} style={{ marginBottom: 'var(--space-1)', fontSize: '1rem' }}>
                                    {participant.displayText}
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <p style={{ margin: 0, color: 'var(--gray-500)', fontStyle: 'italic' }}>
                                No participant information available for this thread.
                              </p>
                            )}
                          </div>

                          {/* Thread Summary */}
                          <div style={{ marginBottom: 'var(--space-5)' }}>
                            <h5 style={{ 
                              color: 'var(--gray-800)', 
                              marginBottom: 'var(--space-2)', 
                              fontSize: '1.1rem',
                              fontWeight: '600',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 'var(--space-2)'
                            }}>
                              <span style={{ 
                                width: '4px', 
                                height: '16px', 
                                backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-500)`,
                                borderRadius: '2px'
                              }}></span>
                              Thread Summary
                            </h5>
                            <div style={{ 
                              padding: 'var(--space-4)', 
                              backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-50)`, 
                              borderRadius: 'var(--radius-md)',
                              border: `1px solid var(--${threadIndex === 0 ? 'blue' : 'green'}-200)`
                            }}>
                              <p style={{ margin: 0, color: 'var(--gray-800)', lineHeight: '1.7', fontSize: '1rem' }}>
                                {thread.summary || 'No detailed summary available for this thread.'}
                              </p>
                            </div>
                          </div>

                          {/* Discussion Agenda */}
                          <div style={{ marginBottom: 'var(--space-5)' }}>
                            <h5 style={{ 
                              color: 'var(--gray-800)', 
                              marginBottom: 'var(--space-2)', 
                              fontSize: '1.1rem',
                              fontWeight: '600',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 'var(--space-2)'
                            }}>
                              <span style={{ 
                                width: '4px', 
                                height: '16px', 
                                backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-500)`,
                                borderRadius: '2px'
                              }}></span>
                              Discussion Agenda
                            </h5>
                            <div style={{ 
                              padding: 'var(--space-4)', 
                              backgroundColor: 'var(--amber-50)', 
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--amber-200)'
                            }}>
                              <p style={{ margin: 0, color: 'var(--amber-800)', lineHeight: '1.7', fontSize: '1rem', fontWeight: '500' }}>
                                {thread.discussion_agenda || thread.reason_for_irrelevancy || 'No agenda information available for this thread.'}
                              </p>
                            </div>
                          </div>

                          {/* Mail Thread Summary - Detailed Email Summaries */}
                          <div>
                            <h5 style={{ 
                              color: 'var(--gray-800)', 
                              marginBottom: 'var(--space-2)', 
                              fontSize: '1.1rem',
                              fontWeight: '600',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 'var(--space-2)'
                            }}>
                              <span style={{ 
                                width: '4px', 
                                height: '16px', 
                                backgroundColor: `var(--${threadIndex === 0 ? 'blue' : 'green'}-500)`,
                                borderRadius: '2px'
                              }}></span>
                              Mail Thread Summary
                            </h5>
                            <div style={{ 
                              padding: 'var(--space-4)', 
                              backgroundColor: 'var(--gray-50)', 
                              borderRadius: 'var(--radius-md)',
                              border: '1px solid var(--gray-200)'
                            }}>
                              {thread.email_summaries && Array.isArray(thread.email_summaries) && thread.email_summaries.length > 0 ? (
                                <ul style={{ margin: 0, paddingLeft: 'var(--space-4)', color: 'var(--gray-700)' }}>
                                  {thread.email_summaries.map((summary, idx) => (
                                    <li key={idx} style={{ marginBottom: 'var(--space-2)', fontSize: '1rem', lineHeight: '1.6' }}>
                                      {summary}
                                    </li>
                                  ))}
                                </ul>
                              ) : (
                                <p style={{ margin: 0, color: 'var(--gray-600)', fontStyle: 'italic' }}>
                                  Detailed email summaries are being processed for this thread.
                                </p>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  );
                })}
              </Section>
            )}
            

          </>
        ) : (
          <div dangerouslySetInnerHTML={{ __html: rawAnalysis }} />
        )}
      </ReportContent>
    </ReportContainer>
  );
}

export default AnalysisReport;
