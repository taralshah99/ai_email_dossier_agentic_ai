import React, { useState } from 'react';
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

const GroupCard = styled.div`
  border: 1px solid #3a3a3a;
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  background-color: #232323;
`;

const GroupHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 8px;
`;

const GroupTitle = styled.h3`
  font-size: 18px;
  font-weight: 600;
  margin: 0;
`;

const TagsRow = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin: 8px 0 12px 0;
`;

const Tag = styled.button`
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid ${props => (props.$active ? '#ff4444' : '#444')};
  background: ${props => (props.$active ? '#3b1f1f' : '#2a2a2a')};
  color: #e0e0e0;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.15s ease-in-out;
  &:hover { border-color: #ff6666; }
`;

const SubSection = styled.div`
  border-top: 1px dashed #3a3a3a;
  padding-top: 10px;
  margin-top: 10px;
`;

const ItemBadgeRow = styled.div`
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  margin: 4px 0 0 0;
`;

const Badge = styled.span`
  display: inline-block;
  padding: 2px 8px;
  font-size: 11px;
  color: #ddd;
  background: #303030;
  border: 1px solid #3f3f3f;
  border-radius: 999px;
`;

function AnalysisReport({ structuredAnalysis, rawAnalysis, productDossier }) {
  const [selectedByGroup, setSelectedByGroup] = useState({});

  const hasStructured = structuredAnalysis && typeof structuredAnalysis === 'object';
  if (!hasStructured && !rawAnalysis && !productDossier) return null;

  const hasGroups = hasStructured && Array.isArray(structuredAnalysis.groups) && structuredAnalysis.groups.length > 0;
  const globalSummary = (hasStructured && structuredAnalysis.global_summary) || null;
  const hasLegacySections = hasStructured && (
    (Array.isArray(structuredAnalysis.thread_subjects) && structuredAnalysis.thread_subjects.length > 0) ||
    (Array.isArray(structuredAnalysis.email_summaries) && structuredAnalysis.email_summaries.length > 0) ||
    (Array.isArray(structuredAnalysis.meeting_agenda) && structuredAnalysis.meeting_agenda.length > 0) ||
    (Array.isArray(structuredAnalysis.meeting_date_time) && structuredAnalysis.meeting_date_time.length > 0) ||
    (!!structuredAnalysis.final_conclusion)
  );

  const findMatchedSubjects = (text, subjects) => {
    if (!text || !Array.isArray(subjects)) return [];
    const lower = String(text).toLowerCase();
    const matches = [];
    for (const s of subjects) {
      if (!s) continue;
      const subj = String(s).toLowerCase();
      if (subj && lower.includes(subj)) matches.push(s);
    }
    return matches;
  };

  const toggleSubject = (groupIdx, subject) => {
    setSelectedByGroup(prev => {
      const cur = new Set(prev[groupIdx] || []);
      if (cur.has(subject)) cur.delete(subject); else cur.add(subject);
      return { ...prev, [groupIdx]: Array.from(cur) };
    });
  };

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

          {structuredAnalysis.product_dossier && (
            <Section>
              <SectionTitle>Product Dossier</SectionTitle>
              <div dangerouslySetInnerHTML={{ __html: structuredAnalysis.product_dossier }} />
            </Section>
          )}

          {structuredAnalysis.product_details && (
            <Section>
              <SectionTitle>Product Details</SectionTitle>
              <div style={{ whiteSpace: 'pre-wrap' }}>
                {structuredAnalysis.product_details}
              </div>
            </Section>
          )}

            {hasGroups ? (
              <>
                {structuredAnalysis.groups.map((group, gIdx) => {
                  const subjects = Array.isArray(group.thread_subjects) ? group.thread_subjects : [];
                  const selected = selectedByGroup[gIdx] || [];
                  const filterActive = selected.length > 0;

                  const filterItems = (items) => {
                    if (!Array.isArray(items)) return [];
                    if (!filterActive) return items;
                    return items.filter(it => findMatchedSubjects(it, subjects).some(s => selected.includes(s)));
                  };

                  const renderList = (title, items, keyPrefix) => (
                    Array.isArray(items) && items.length > 0 && (
                      <SubSection>
                        <p><strong>{title}:</strong></p>
                        <ul>
                          {items.map((item, idx) => {
                            const matchBadges = findMatchedSubjects(item, subjects);
                            return (
                              <li key={`${keyPrefix}-${gIdx}-${idx}`}>
                                {item}
                                {matchBadges.length > 0 && (
                                  <ItemBadgeRow>
                                    {matchBadges.map((mb, mbIdx) => (
                                      <Badge key={`${keyPrefix}-mb-${gIdx}-${idx}-${mbIdx}`}>{mb}</Badge>
                                    ))}
                                  </ItemBadgeRow>
                                )}
                              </li>
                            );
                          })}
                        </ul>
                      </SubSection>
                    )
                  );

                  return (
                    <GroupCard key={`group-${gIdx}`}>
                      <GroupHeader>
                        <GroupTitle>{group.title || `Group ${gIdx + 1}`}</GroupTitle>
                      </GroupHeader>

                      {subjects.length > 0 && (
                        <>
                          <p><strong>Threads included:</strong></p>
                          <TagsRow>
                            {subjects.map((s, sIdx) => (
                              <Tag
                                key={`subject-${gIdx}-${sIdx}`}
                                $active={selected.includes(s)}
                                onClick={() => toggleSubject(gIdx, s)}
                                title={selected.includes(s) ? 'Click to unselect' : 'Click to filter by this thread'}
                              >
                                {s}
                              </Tag>
                            ))}
                            {selected.length > 0 && (
                              <Tag onClick={() => setSelectedByGroup(prev => ({ ...prev, [gIdx]: [] }))}>
                                Clear filter
                              </Tag>
                            )}
                          </TagsRow>
                        </>
                      )}

                      {Array.isArray(group.products) && group.products.length > 0 && (
                      <div>
                        <p><strong>Products:</strong></p>
                        <ul>
                          {group.products.map((p, pIdx) => (
                            <li key={`gp-${gIdx}-${pIdx}`}>{p?.name || 'Unknown'}{p?.domain ? ` — ${p.domain}` : ''}</li>
                          ))}
                        </ul>
                      </div>
                      )}

                      {renderList('Email Summaries', filterItems(group.email_summaries), 'ges')}
                      {renderList('Meeting Agenda', filterItems(group.meeting_agenda), 'gma')}
                      {renderList('Meeting Date & Time', filterItems(group.meeting_date_time), 'gmdt')}

                      {group.final_conclusion && (
                        <SubSection>
                          <p><strong>Conclusion:</strong> {group.final_conclusion}</p>
                        </SubSection>
                      )}
                    </GroupCard>
                  );
                })}

                {globalSummary && (
                  <Section>
                    <SectionTitle>Global Summary</SectionTitle>
                    {globalSummary.final_conclusion && (
                      <p>{globalSummary.final_conclusion}</p>
                    )}
                    {Array.isArray(globalSummary.products) && globalSummary.products.length > 0 && (
                      <div>
                        <p><strong>Products:</strong></p>
                        <ul>
                          {globalSummary.products.map((p, idx) => (
                            <li key={`gs-p-${idx}`}>{p?.name || 'Unknown'}{p?.domain ? ` — ${p.domain}` : ''}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </Section>
                )}
              </>
            ) : hasLegacySections ? (
              <>
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
            ) : null}

            {productDossier && (
              <Section>
                <SectionTitle>Product Dossier</SectionTitle>
                <div dangerouslySetInnerHTML={{ __html: productDossier }} />
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
