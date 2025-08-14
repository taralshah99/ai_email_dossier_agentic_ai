import React, { useMemo, useState } from 'react';
import styled from 'styled-components';
import { Check, Mail, ChevronDown, ChevronUp } from 'lucide-react';

const ResultsContainer = styled.div`
  width: 100%;
  max-width: 800px;
  margin-top: 20px;
`;

const ThreadList = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;

const ThreadItem = styled.div`
  display: flex;
  align-items: flex-start;
  gap: 15px;
  padding: 15px;
  background-color: #2a2a2a;
  border: 1px solid ${props => props.selected ? '#ff4444' : '#404040'};
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  
  &:hover {
    border-color: #ff4444;
    background-color: #333;
  }
`;

const Checkbox = styled.button`
  width: 20px;
  height: 20px;
  border: 2px solid ${props => props.selected ? '#ff4444' : '#666'};
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background-color: ${props => props.selected ? '#ff4444' : 'transparent'};
  cursor: pointer;
`;

const ThreadInfo = styled.div`
  flex: 1;
`;

const Subject = styled.h3`
  font-size: 16px;
  font-weight: 500;
  color: #ffffff;
  margin: 0 0 5px 0;
`;

const Sender = styled.p`
  font-size: 14px;
  color: #888;
  margin: 0;
`;

const ProductDossierPreview = styled.div`
  font-size: 12px;
  color: #bbb;
  margin-top: 4px;
  border-left: 2px solid #444;
  padding-left: 8px;
  max-height: 48px;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const Snippet = styled.p`
  font-size: 13px;
  color: #aaa;
  margin: 4px 0 0 0;
  white-space: ${props => (props.$expanded ? 'pre-wrap' : 'nowrap')};
  overflow: hidden;
  text-overflow: ellipsis;
`;

const ToggleSnippetButton = styled.button`
  background: transparent;
  border: 1px solid #444;
  color: #ddd;
  border-radius: 6px;
  padding: 4px 8px;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  margin-top: 6px;
  transition: all 0.15s ease-in-out;
  &:hover { border-color: #ff6666; color: #fff; }
  
  &:disabled {
    background: #333333;
    color: #888888;
    border-color: #555555;
    cursor: not-allowed;
    opacity: 0.6;
    transform: scale(0.95);
  }
`;

const LoadingSpinner = styled.div`
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 3px solid #ffffff;
  border-radius: 50%;
  border-top-color: transparent;
  animation: spin 1s ease-in-out infinite;
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const Toolbar = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
`;

const Actions = styled.div`
  display: flex;
  align-items: center;
  gap: 12px;
`;

function SearchResults({ results, selectedThreads, onThreadToggle, onAnalyzeSelected, isLoading }) {
  const [sortBy, setSortBy] = useState('subject');
  const [expanded, setExpanded] = useState({});

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

  return (
    <ResultsContainer>
      <Toolbar>
        <div>{results.length} results</div>
        <Actions>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
            <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} />
            Select all
          </label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} style={{ background: '#2a2a2a', color: '#fff', border: '1px solid #404040', borderRadius: 6, padding: '6px 8px' }}>
            <option value="subject">Sort by Subject</option>
            <option value="sender">Sort by Sender</option>
          </select>
        </Actions>
      </Toolbar>
      <ThreadList>
        {sortedResults.map(thread => (
          <ThreadItem
            key={thread.id}
            selected={selectedThreads.includes(thread.id)}
            onClick={() => onThreadToggle(thread.id)}
          >
            <Checkbox
              selected={selectedThreads.includes(thread.id)}
              onClick={(e) => { e.stopPropagation(); onThreadToggle(thread.id); }}
              role="checkbox"
              aria-checked={selectedThreads.includes(thread.id)}
              aria-label={selectedThreads.includes(thread.id) ? 'Deselect thread' : 'Select thread'}
            >
              {selectedThreads.includes(thread.id) && <Check size={14} />}
            </Checkbox>
            <ThreadInfo>
              <Subject>{thread.subject || 'No Subject'}</Subject>
              <Sender>{thread.sender || 'Unknown Sender'}</Sender>

              {/* New: Product Dossier Preview */}
              {thread.product_dossier && (
                <ProductDossierPreview
                  dangerouslySetInnerHTML={{ __html: thread.product_dossier }}
                />
              )}

              {getCleanBody(thread) && (
                <>
                  {expanded[thread.id] && (
                    <Snippet $expanded>
                      {getPreviewText(thread, true)}
                    </Snippet>
                  )}
                  <ToggleSnippetButton
                    onClick={(e) => { e.stopPropagation(); toggleExpand(thread.id); }}
                    aria-label={expanded[thread.id] ? 'Show less' : 'Show more'}
                  >
                    {expanded[thread.id] ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                    {expanded[thread.id] ? 'Show less' : 'Show more'}
                  </ToggleSnippetButton>
                </>
              )}
            </ThreadInfo>
            <Mail size={20} color="#666" />
          </ThreadItem>
        ))}
      </ThreadList>
    </ResultsContainer>
  );
}

export default SearchResults;
