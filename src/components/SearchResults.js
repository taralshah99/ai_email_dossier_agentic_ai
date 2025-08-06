import React from 'react';
import styled from 'styled-components';
import { Check, Mail } from 'lucide-react';

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
  align-items: center;
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

const Checkbox = styled.div`
  width: 24px;
  height: 24px;
  border: 2px solid ${props => props.selected ? '#ff4444' : '#666'};
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  background-color: ${props => props.selected ? '#ff4444' : 'transparent'};
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

const AnalyzeButton = styled.button`
  padding: 12px 24px;
  background-color: #ff4444;
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  margin-top: 20px;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #ff6666;
  }
  
  &:disabled {
    background-color: #666;
    cursor: not-allowed;
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

function SearchResults({ results, selectedThreads, onThreadToggle, onAnalyzeSelected, isLoading }) {
  return (
    <ResultsContainer>
      <ThreadList>
        {results.map(thread => (
          <ThreadItem
            key={thread.id}
            selected={selectedThreads.includes(thread.id)}
            onClick={() => onThreadToggle(thread.id)}
          >
            <Checkbox selected={selectedThreads.includes(thread.id)}>
              {selectedThreads.includes(thread.id) && <Check size={16} />}
            </Checkbox>
            <ThreadInfo>
              <Subject>{thread.subject || 'No Subject'}</Subject>
              <Sender>{thread.sender || 'Unknown Sender'}</Sender>
            </ThreadInfo>
            <Mail size={20} color="#666" />
          </ThreadItem>
        ))}
      </ThreadList>
      
      {selectedThreads.length > 0 && (
        <AnalyzeButton onClick={onAnalyzeSelected} disabled={isLoading}>
          {isLoading ? (
            <>
              <LoadingSpinner />
              Analyzing...
            </>
          ) : (
            <>
              <Mail size={20} />
              Analyze Selected Threads ({selectedThreads.length})
            </>
          )}
        </AnalyzeButton>
      )}
    </ResultsContainer>
  );
}

export default SearchResults;