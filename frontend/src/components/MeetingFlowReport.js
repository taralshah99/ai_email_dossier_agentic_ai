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

const AgendaList = styled.ol`
  margin: var(--space-3) 0;
  padding-left: var(--space-5);
  
  li {
    margin-bottom: var(--space-2);
    color: var(--gray-700);
    font-weight: 500;
  }
`;

function MeetingFlowReport({ meetingFlowData }) {
  if (!meetingFlowData || !meetingFlowData.meeting_flow) {
    return null;
  }

  // Parse the meeting flow text into structured sections
  const parseMeetingFlow = (text) => {
    const sections = {};
    const lines = text.split('\n').filter(line => line.trim());
    
    let currentSection = null;
    let currentContent = [];
    let meetingDateTime = null;
    
    // First pass: Look for meeting date/time information
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Look for date/time patterns in the content
      const dateTimePatterns = [
        /meeting.*(?:on|at|scheduled for|will be held)\s*(.*?(?:am|pm|AM|PM|\d{1,2}:\d{2}|\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}|monday|tuesday|wednesday|thursday|friday|saturday|sunday|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).*?)(?:\.|$)/i,
        /(?:date|time|when|schedule):\s*(.*?(?:am|pm|AM|PM|\d{1,2}:\d{2}|\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}|monday|tuesday|wednesday|thursday|friday|saturday|sunday|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).*?)(?:\.|$)/i,
        /^-\s*(?:date|time|when|schedule):\s*(.*?)$/i,
        /^-\s*(.*?(?:am|pm|AM|PM|\d{1,2}:\d{2}|\d{1,2}\/\d{1,2}\/\d{4}|\d{4}-\d{2}-\d{2}|monday|tuesday|wednesday|thursday|friday|saturday|sunday).*?)$/i
      ];
      
      for (const pattern of dateTimePatterns) {
        const match = trimmedLine.match(pattern);
        if (match && match[1] && match[1].trim()) {
          meetingDateTime = match[1].trim();
          break;
        }
      }
      
      if (meetingDateTime) break;
    }
    
    // Second pass: Parse sections normally
    for (const line of lines) {
      const trimmedLine = line.trim();
      
      // Skip lines that were identified as date/time info
      if (meetingDateTime && trimmedLine.toLowerCase().includes(meetingDateTime.toLowerCase())) {
        continue;
      }
      
      // Check if this is a section header (no leading dash and not empty)
      if (!trimmedLine.startsWith('-') && !trimmedLine.startsWith('1.') && 
          !trimmedLine.startsWith('2.') && !trimmedLine.startsWith('3.') &&
          trimmedLine.length > 0 && 
          !trimmedLine.match(/^[a-z]/) && // Not starting with lowercase (likely continuation)
          trimmedLine !== 'Meeting Flow Dossier') {
        
        // Save previous section
        if (currentSection && currentContent.length > 0) {
          sections[currentSection] = currentContent;
        }
        
        // Start new section
        currentSection = trimmedLine;
        currentContent = [];
      } else if (trimmedLine && currentSection) {
        // Add content to current section
        currentContent.push(trimmedLine);
      }
    }
    
    // Save the last section
    if (currentSection && currentContent.length > 0) {
      sections[currentSection] = currentContent;
    }
    
    return { sections, meetingDateTime };
  };

  const { sections, meetingDateTime } = parseMeetingFlow(meetingFlowData.meeting_flow);

  const renderContent = (content) => {
    return content.map((item, index) => {
      const cleanItem = item.replace(/^[-•]\s*/, ''); // Remove leading dashes/bullets
      
      // Check if it's a numbered agenda item
      if (cleanItem.match(/^\d+\.\s/)) {
        return <li key={index}>{cleanItem.replace(/^\d+\.\s/, '')}</li>;
      }
      
      // Regular bullet point
      return <li key={index}>{cleanItem}</li>;
    });
  };

  return (
    <ReportContainer>
      <ReportTitle>Meeting Flow Dossier</ReportTitle>
      <ReportContent>
        {/* Meeting Date and Time - First section if available */}
        {meetingDateTime && (
          <Section>
            <SectionTitle>Meeting Date and Time</SectionTitle>
            <p>{meetingDateTime}</p>
          </Section>
        )}
        
        {Object.entries(sections).map(([sectionTitle, content]) => (
          <Section key={sectionTitle}>
            <SectionTitle>{sectionTitle}</SectionTitle>
            
            {sectionTitle.toLowerCase().includes('agenda') ? (
              <AgendaList>
                {renderContent(content)}
              </AgendaList>
            ) : (
              <ul>
                {renderContent(content)}
              </ul>
            )}
          </Section>
        ))}
        
        {/* Fallback if no sections are parsed */}
        {Object.keys(sections).length === 0 && !meetingDateTime && (
          <div dangerouslySetInnerHTML={{ 
            __html: meetingFlowData.meeting_flow?.replace(/\n/g, '<br>') || '' 
          }} />
        )}
      </ReportContent>
    </ReportContainer>
  );
}

export default MeetingFlowReport;
