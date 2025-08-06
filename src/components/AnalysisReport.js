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

function AnalysisReport({ analysis }) {
  if (!analysis) return null;

  return (
    <ReportContainer>
      <ReportTitle>Analysis Report</ReportTitle>
      <ReportContent>
        {/* If the analysis is already HTML formatted */}
        {typeof analysis === 'string' ? (
          <div dangerouslySetInnerHTML={{ __html: analysis }} />
        ) : (
          // If the analysis is an object with sections
          Object.entries(analysis).map(([title, content]) => (
            <Section key={title}>
              <SectionTitle>{title}</SectionTitle>
              <div dangerouslySetInnerHTML={{ __html: content }} />
            </Section>
          ))
        )}
      </ReportContent>
    </ReportContainer>
  );
}

export default AnalysisReport;