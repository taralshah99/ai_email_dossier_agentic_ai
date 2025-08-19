import React, { useMemo, useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { Check, Mail, ChevronDown, ChevronUp, User, Hash, Eye, EyeOff } from 'lucide-react';

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

const ResultsContainer = styled.div`
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-8);
  animation: ${fadeInUp} 0.6s ease-out;
`;

const ResultsHeader = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-6);
  padding: var(--space-4) var(--space-6);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-sm);
`;

const ResultsCount = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-700);
  
  .count {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 24px;
    height: 24px;
    background: var(--primary-100);
    color: var(--primary-800);
    border-radius: var(--radius-md);
    padding: 0 var(--space-2);
    font-size: 0.75rem;
    font-weight: 700;
  }
`;

const ThreadList = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
`;

const ThreadItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: var(--space-4);
  padding: var(--space-6);
  background: white;
  border: 1px solid ${props => props.selected ? 'var(--primary-300)' : 'var(--gray-200)'};
  border-radius: var(--radius-xl);
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
  
  &::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: ${props => props.selected ? 'var(--primary-500)' : 'transparent'};
    transition: all var(--transition-fast);
  }
  
  &:hover {
    border-color: var(--primary-300);
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
    
    &::before {
      background: var(--primary-400);
    }
  }
  
  &.selected {
    background: var(--primary-50);
    border-color: var(--primary-300);
    
    &::before {
      background: var(--primary-500);
    }
  }
`;

const Checkbox = styled.button`
  width: 20px;
  height: 20px;
  border: 2px solid ${props => props.selected ? '#ff8c00' : '#cccccc'};
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background-color: ${props => props.selected ? '#ff8c00' : 'transparent'};
  cursor: pointer;
`;

const ThreadInfo = styled.div`
  flex: 1;
`;

const Subject = styled.h3`
  font-size: 16px;
  font-weight: 500;
  color: #333333;
  margin: 0 0 5px 0;
`;

const Sender = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 0.75rem;
  color: var(--gray-600);
  font-weight: 500;
  
  svg {
    width: 14px;
    height: 14px;
    color: var(--gray-500);
  }
`;

const MetadataContainer = styled.div`
  margin-top: 8px;
  padding: 8px;
  background-color: #f8f8f8;
  border-radius: 4px;
  border-left: 3px solid #ff8c00;
`;

const MetadataRow = styled.div`
  display: flex;
  gap: 16px;
  margin-bottom: 4px;
  font-size: 12px;
  
  &:last-child {
    margin-bottom: 0;
  }
`;

const MetadataLabel = styled.span`
  color: #666666;
  min-width: 80px;
`;

const MetadataValue = styled.span`
  color: #333333;
`;

const ParticipantsList = styled.div`
  margin-top: 4px;
`;

const Participant = styled.div`
  font-size: 11px;
  color: #666666;
  margin: 2px 0;
  padding-left: 12px;
`;



const Snippet = styled.p`
  font-size: 13px;
  color: #aaa;
  margin: 4px 0 0 0;
  white-space: ${props => (props.$expanded ? 'pre-wrap' : 'nowrap')};
  overflow: hidden;
  text-overflow: ellipsis;
`;



const Controls = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-4);
  flex-wrap: wrap;
  
  @media (max-width: 640px) {
    flex-direction: column;
    align-items: stretch;
    gap: var(--space-3);
  }
`;

const SelectAllControl = styled.label`
  display: flex;
  align-items: center;
  gap: var(--space-2);
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--gray-700);
  
  input[type="checkbox"] {
    width: 18px;
    height: 18px;
    accent-color: var(--primary-500);
  }
`;

const SortSelect = styled.select`
  padding: var(--space-2) var(--space-3);
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:focus {
    outline: none;
    border-color: var(--primary-500);
    box-shadow: 0 0 0 3px var(--primary-100);
  }
  
  &:hover {
    border-color: var(--gray-400);
  }
`;

const ThreadHeader = styled.div`
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-3);
  margin-bottom: var(--space-2);
`;

const ThreadMeta = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-4);
  margin-bottom: var(--space-3);
  flex-wrap: wrap;
`;

const MetaItem = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 0.75rem;
  color: var(--gray-600);
  
  svg {
    width: 14px;
    height: 14px;
    color: var(--gray-500);
  }
`;

// Update Sender to extend MetaItem
const SenderMeta = styled(MetaItem)`
  font-weight: 500;
`;

const ActionButtons = styled.div`
  display: flex;
  gap: var(--space-2);
  margin-top: var(--space-3);
  flex-wrap: wrap;
`;

const ActionButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-2) var(--space-3);
  background: white;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  color: var(--gray-700);
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:hover:not(:disabled) {
    background: var(--gray-50);
    border-color: var(--primary-300);
    color: var(--primary-700);
  }
  
  &:disabled {
    background: var(--gray-100);
    color: var(--gray-400);
    border-color: var(--gray-200);
    cursor: not-allowed;
  }
  
  svg {
    width: 14px;
    height: 14px;
  }
`;

function SearchResults({ results, selectedThreads, onThreadToggle, onProcessSelected, isLoading }) {
  const [sortBy, setSortBy] = useState('subject');
  const [expanded, setExpanded] = useState({});
  const [showMetadata, setShowMetadata] = useState({});

  const sortedResults = useMemo(() => {
    const copy = [...results];
    if (sortBy === 'sender') {
      copy.sort((a, b) => (a.sender || '').localeCompare(b.sender || ''));
    } else {
      copy.sort((a, b) => (a.subject || '').localeCompare(b.subject || ''));
    }
    return copy;
  }, [results, sortBy]);

  const allSelected = useMemo(() => results.length > 0 && selectedThreads.length === results.length, [selectedThreads, results.length]);

  const toggleSelectAll = () => {
    if (results.length === 0) return;
    if (allSelected) {
      selectedThreads.forEach(id => onThreadToggle(id));
    } else {
      results.forEach(t => { if (!selectedThreads.includes(t.id)) onThreadToggle(t.id); });
    }
  };

  const getCleanBody = (thread) => {
    const rawBody = String(thread.body || '').trim();
    const subj = String(thread.subject || '').trim();
    if (!rawBody) return '';
    if (subj) {
      const bodyLower = rawBody.toLowerCase();
      const subjLower = subj.toLowerCase();
      if (bodyLower.startsWith(subjLower)) {
        const stripped = rawBody.slice(subj.length).replace(/^[\s:\-–—]+/, '').trim();
        return stripped;
      }
    }
    return rawBody;
  };

  const getPreviewText = (thread, isExpanded) => {
    const raw = getCleanBody(thread);
    if (isExpanded) return raw.trim();
    const maxLen = 220;
    const t = raw.replace(/\s+/g, ' ').trim();
    return t.length > maxLen ? `${t.slice(0, maxLen)}…` : t;
  };

  const toggleExpand = (id) => {
    setExpanded(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const toggleMetadata = (id) => {
    setShowMetadata(prev => ({ ...prev, [id]: !prev[id] }));
  };

  const renderThreadMetadata = (thread) => {
    // For now, we'll show basic info from the thread object
    // Later this will be enhanced when we get metadata from the backend
    const participants = [];
    
    // Extract basic participant info from sender
    if (thread.sender) {
      participants.push({ email: thread.sender, role: 'sender' });
    }

    return (
      <MetadataContainer>
        <MetadataRow>
          <MetadataLabel>Thread ID:</MetadataLabel>
          <MetadataValue>{thread.id}</MetadataValue>
        </MetadataRow>
        <MetadataRow>
          <MetadataLabel>Subject:</MetadataLabel>
          <MetadataValue>{thread.subject || 'No Subject'}</MetadataValue>
        </MetadataRow>
        {participants.length > 0 && (
          <MetadataRow>
            <MetadataLabel>Participants:</MetadataLabel>
            <div>
              <MetadataValue>{participants.length} participant(s)</MetadataValue>
              <ParticipantsList>
                {participants.map((participant, idx) => (
                  <Participant key={idx}>
                    • {participant.email} ({participant.role})
                  </Participant>
                ))}
              </ParticipantsList>
            </div>
          </MetadataRow>
        )}
        <MetadataRow>
          <MetadataLabel>Preview:</MetadataLabel>
          <MetadataValue>{thread.body ? 'Content available' : 'No content preview'}</MetadataValue>
        </MetadataRow>
      </MetadataContainer>
    );
  };

  return (
    <ResultsContainer>
      <ResultsHeader>
        <ResultsCount>
          <Mail size={16} />
          <span className="count">{results.length}</span>
          {results.length === 1 ? 'result' : 'results'}
        </ResultsCount>
        <Controls>
          <SelectAllControl>
            <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} />
            Select all
          </SelectAllControl>
          <SortSelect value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <option value="subject">Sort by Subject</option>
            <option value="sender">Sort by Sender</option>
          </SortSelect>
        </Controls>
      </ResultsHeader>
      <ThreadList>
        {sortedResults.map(thread => (
          <ThreadItem
            key={thread.id}
            selected={selectedThreads.includes(thread.id)}
            className={selectedThreads.includes(thread.id) ? 'selected' : ''}
            onClick={() => onThreadToggle(thread.id)}
          >
            <Checkbox
              selected={selectedThreads.includes(thread.id)}
              onClick={(e) => { e.stopPropagation(); onThreadToggle(thread.id); }}
              role="checkbox"
              aria-checked={selectedThreads.includes(thread.id)}
              aria-label={selectedThreads.includes(thread.id) ? 'Deselect thread' : 'Select thread'}
            >
              {selectedThreads.includes(thread.id) && <Check size={16} />}
            </Checkbox>
            
            <ThreadInfo>
              <ThreadHeader>
                <Subject>{thread.subject || 'No Subject'}</Subject>
                <Mail size={18} color="var(--gray-400)" />
              </ThreadHeader>
              
              <ThreadMeta>
                <SenderMeta>
                  <User size={14} />
                  {thread.sender || 'Unknown Sender'}
                </SenderMeta>
                <MetaItem>
                  <Hash size={14} />
                  ID: {thread.id}
                </MetaItem>
              </ThreadMeta>

              <ActionButtons>
                <ActionButton
                  onClick={(e) => { e.stopPropagation(); toggleMetadata(thread.id); }}
                  aria-label={showMetadata[thread.id] ? 'Hide metadata' : 'Show metadata'}
                >
                  {showMetadata[thread.id] ? <EyeOff size={14} /> : <Eye size={14} />}
                  {showMetadata[thread.id] ? 'Hide Details' : 'Show Details'}
                </ActionButton>
                
                {getCleanBody(thread) && (
                  <ActionButton
                    onClick={(e) => { e.stopPropagation(); toggleExpand(thread.id); }}
                    aria-label={expanded[thread.id] ? 'Hide content' : 'Show content'}
                  >
                    {expanded[thread.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    {expanded[thread.id] ? 'Hide Content' : 'Show Content'}
                  </ActionButton>
                )}
              </ActionButtons>

              {/* Show metadata when toggled */}
              {showMetadata[thread.id] && renderThreadMetadata(thread)}

              {/* Show content when toggled */}
              {expanded[thread.id] && getCleanBody(thread) && (
                <Snippet $expanded>
                  {getPreviewText(thread, true)}
                </Snippet>
              )}
            </ThreadInfo>
          </ThreadItem>
        ))}
      </ThreadList>
    </ResultsContainer>
  );
}

export default SearchResults;
