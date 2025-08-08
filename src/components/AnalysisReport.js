import React from 'react';
import styled from 'styled-components';

const ReportContainer = styled.div`
  width: 100%;
  max-width: 800px;
  margin-top: 30px;
  padding: 25px;
  background-color: #2a2a2a;
  border-radius: 8px;
  border: 1px solid #404040;
`;

const ReportTitle = styled.h2`
  font-size: 24px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 20px 0;
`;

const ReportContent = styled.div`
  color: #e0e0e0;
  line-height: 1.6;
  
  h1, h2, h3 {
    color: #ffffff;
    margin: 16px 0 8px 0;
  }
  
  h1 { font-size: 20px; }
  h2 { font-size: 18px; }
  h3 { font-size: 16px; }
  
  strong {
    color: #ffffff;
    font-weight: 600;
  }
  
  em { font-style: italic; }
  
  ul {
    margin: 8px 0;
    padding-left: 20px;
  }
  
  li { margin-bottom: 4px; }
  
  p { margin: 8px 0; }
`;

const Section = styled.div`
  margin-bottom: 20px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const SectionTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  color: #ffffff;
  margin: 0 0 12px 0;
`;

function AnalysisReport({ structuredAnalysis, rawAnalysis }) {
  const hasStructured = structuredAnalysis && typeof structuredAnalysis === 'object';

  if (!hasStructured && !rawAnalysis) return null;

  return (
    <ReportContainer>
      <ReportTitle>Analysis Report</ReportTitle>
      <ReportContent>
        {hasStructured ? (
          <>
            {(structuredAnalysis.product_name || structuredAnalysis.product_domain) && (
              <Section>
                <SectionTitle>Product</SectionTitle>
                <div>
                  {structuredAnalysis.product_name && (
                    <p><strong>Name:</strong> {structuredAnalysis.product_name}</p>
                  )}
                  {structuredAnalysis.product_domain && (
                    <p><strong>Domain:</strong> {structuredAnalysis.product_domain}</p>
                  )}
                </div>
              </Section>
            )}

            {Array.isArray(structuredAnalysis.thread_subjects) && structuredAnalysis.thread_subjects.length > 0 && (
              <Section>
                <SectionTitle>Thread Subjects</SectionTitle>
                <ul>
                  {structuredAnalysis.thread_subjects.map((item, idx) => (
                    <li key={`ts-${idx}`}>{item}</li>
                  ))}
                </ul>
              </Section>
            )}

            {Array.isArray(structuredAnalysis.email_summaries) && structuredAnalysis.email_summaries.length > 0 && (
              <Section>
                <SectionTitle>Email Summaries</SectionTitle>
                <ul>
                  {structuredAnalysis.email_summaries.map((item, idx) => (
                    <li key={`es-${idx}`}>{item}</li>
                  ))}
                </ul>
              </Section>
            )}

            {Array.isArray(structuredAnalysis.meeting_agenda) && structuredAnalysis.meeting_agenda.length > 0 && (
              <Section>
                <SectionTitle>Meeting Agenda</SectionTitle>
                <ul>
                  {structuredAnalysis.meeting_agenda.map((item, idx) => (
                    <li key={`ma-${idx}`}>{item}</li>
                  ))}
                </ul>
              </Section>
            )}

            {Array.isArray(structuredAnalysis.meeting_date_time) && structuredAnalysis.meeting_date_time.length > 0 && (
              <Section>
                <SectionTitle>Meeting Date & Time</SectionTitle>
                <ul>
                  {structuredAnalysis.meeting_date_time.map((item, idx) => (
                    <li key={`mdt-${idx}`}>{item}</li>
                  ))}
                </ul>
              </Section>
            )}

            {structuredAnalysis.final_conclusion && (
              <Section>
                <SectionTitle>Final Conclusion</SectionTitle>
                <div>
                  <p>{structuredAnalysis.final_conclusion}</p>
                </div>
              </Section>
            )}
          </>
        ) : (
          // Fallback to raw formatted string/HTML
          <div dangerouslySetInnerHTML={{ __html: rawAnalysis }} />
        )}
      </ReportContent>
    </ReportContainer>
  );
}

export default AnalysisReport;