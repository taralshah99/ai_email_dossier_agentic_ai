import React, { useMemo, useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { Check, Mail, ChevronDown, ChevronUp, User, Hash, Eye, EyeOff, Users, MessageSquare, Sparkles, XCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

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

const spin = keyframes`
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
`;

const ResultsContainer = styled.div`
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-8);
  animation: ${fadeInUp} 0.6s ease-out;
  padding-bottom: ${props => props.$hasSelectedThreads ? '120px' : '0'};
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

// New styled components for badges
const BadgeContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-2);
  margin-top: var(--space-2);
`;

const Badge = styled.span`
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  background: ${props => {
    if (props.$isCurrentUser) {
      return '#dcfce7'; /* Light green background */
    }
    switch (props.$type) {
      case 'sender': return 'var(--primary-100)';
      case 'cc': return 'var(--warning-100)';
      case 'bcc': return 'var(--error-100)';
      default: return 'var(--gray-100)';
    }
  }};
  color: ${props => {
    if (props.$isCurrentUser) {
      return '#166534'; /* Dark green text */
    }
    switch (props.$type) {
      case 'sender': return 'var(--primary-800)';
      case 'cc': return 'var(--warning-800)';
      case 'bcc': return 'var(--error-800)';
      default: return 'var(--gray-700)';
    }
  }};
  border: 1px solid ${props => {
    if (props.$isCurrentUser) {
      return '#bbf7d0'; /* Medium green border */
    }
    switch (props.$type) {
      case 'sender': return 'var(--primary-200)';
      case 'cc': return 'var(--warning-200)';
      case 'bcc': return 'var(--error-200)';
      default: return 'var(--gray-200)';
    }
  }};
  border-radius: var(--radius-sm);
  font-size: 0.75rem;
  font-weight: 500;
  
  svg {
    width: 12px;
    height: 12px;
  }
`;

const ParticipantsSection = styled.div`
  margin-top: var(--space-3);
`;

const ParticipantsTitle = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-1);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--gray-700);
  margin-bottom: var(--space-2);
  
  svg {
    width: 14px;
    height: 14px;
  }
`;

// Sticky Process Button Container
const StickyProcessContainer = styled.div`
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: linear-gradient(to top, rgba(255, 255, 255, 0.95), rgba(255, 255, 255, 0.8));
  backdrop-filter: blur(10px);
  border-top: 1px solid var(--gray-200);
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-xl) var(--radius-xl) 0 0;
  box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-4);
  
  @media (max-width: 640px) {
    flex-direction: column;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
  }
`;

const ProcessButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-4) var(--space-8);
  background: var(--primary-500);
  color: white;
  border: none;
  border-radius: var(--radius-xl);
  font-size: 1rem;
  font-weight: 700;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-lg);
  min-height: 56px;
  
  &:hover:not(:disabled) {
    background: var(--primary-600);
    transform: translateY(-3px);
    box-shadow: var(--shadow-xl);
  }
  
  &:active:not(:disabled) {
    transform: translateY(-1px);
  }
  
  &:disabled {
    background: var(--gray-400);
    cursor: not-allowed;
    transform: none;
    box-shadow: var(--shadow-sm);
  }
  
  svg {
    width: 22px;
    height: 22px;
  }
  
  .animate-spin {
    animation: ${spin} 1s linear infinite;
  }
  
  @media (max-width: 640px) {
    width: 100%;
    justify-content: center;
    padding: var(--space-4) var(--space-6);
    font-size: 0.95rem;
  }
`;

const ClearButton = styled.button`
  display: inline-flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-3) var(--space-4);
  background: white;
  color: var(--gray-700);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:hover:not(:disabled) {
    background: var(--gray-50);
    border-color: var(--gray-400);
  }
  
  &:disabled {
    background: var(--gray-100);
    color: var(--gray-400);
    border-color: var(--gray-200);
    cursor: not-allowed;
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
  
  @media (max-width: 640px) {
    width: 100%;
    justify-content: center;
  }
`;

const SelectionInfo = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  color: var(--gray-600);
  font-weight: 500;
  
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
  
  @media (max-width: 640px) {
    justify-content: center;
  }
`;

function SearchResults({ results, selectedThreads, onThreadToggle, onProcessSelected, isLoading }) {
  const { user } = useAuth();
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

  // Extract participants from thread data
  const getParticipants = (thread) => {
    const participants = [];
    const seenEmails = new Set(); // Track seen emails to avoid duplicates
    
    // Use the new participants data from backend if available
    if (thread.participants) {
      // Add sender
      if (thread.participants.sender && Array.isArray(thread.participants.sender)) {
        thread.participants.sender.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'sender', type: 'sender' });
            seenEmails.add(emailLower);
          }
        });
      }
      
      // Add CC recipients
      if (thread.participants.cc && Array.isArray(thread.participants.cc)) {
        thread.participants.cc.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'cc', type: 'cc' });
            seenEmails.add(emailLower);
          }
        });
      }
      
      // Add BCC recipients
      if (thread.participants.bcc && Array.isArray(thread.participants.bcc)) {
        thread.participants.bcc.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'bcc', type: 'bcc' });
            seenEmails.add(emailLower);
          }
        });
      }
      
      // Add recipients
      if (thread.participants.recipients && Array.isArray(thread.participants.recipients)) {
        thread.participants.recipients.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'recipient', type: 'recipient' });
            seenEmails.add(emailLower);
          }
        });
      }
    } else {
      // Fallback to old method if participants data is not available
      if (thread.sender) {
        const emailLower = thread.sender.toLowerCase();
        if (!seenEmails.has(emailLower)) {
          participants.push({ email: thread.sender, role: 'sender', type: 'sender' });
          seenEmails.add(emailLower);
        }
      }
      
      if (thread.cc && Array.isArray(thread.cc)) {
        thread.cc.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'cc', type: 'cc' });
            seenEmails.add(emailLower);
          }
        });
      }
      
      if (thread.bcc && Array.isArray(thread.bcc)) {
        thread.bcc.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'bcc', type: 'bcc' });
            seenEmails.add(emailLower);
          }
        });
      }
      
      if (thread.recipients && Array.isArray(thread.recipients)) {
        thread.recipients.forEach(email => {
          const emailLower = email.toLowerCase();
          if (!seenEmails.has(emailLower)) {
            participants.push({ email, role: 'recipient', type: 'recipient' });
            seenEmails.add(emailLower);
          }
        });
      }
    }
    
    // Mark current user in their appropriate role if they're already in the participants list
    if (user && user.email) {
      const userEmail = user.email.toLowerCase();
      participants.forEach(participant => {
        if (participant.email.toLowerCase() === userEmail) {
          participant.isCurrentUser = true;
        }
      });
    }
    
    return participants;
  };

  const renderThreadMetadata = (thread) => {
    const participants = getParticipants(thread);
    const mailCount = thread.message_count || thread.mail_count || 1; // Default to 1 if not available
    
    // Group participants by type
    const senderParticipants = participants.filter(p => p.type === 'sender');
    const ccParticipants = participants.filter(p => p.type === 'cc');
    const bccParticipants = participants.filter(p => p.type === 'bcc');
    const recipientParticipants = participants.filter(p => p.type === 'recipient');

    return (
      <MetadataContainer>
        <MetadataRow>
          <MetadataLabel>Mail Count:</MetadataLabel>
          <MetadataValue>{mailCount} email(s)</MetadataValue>
        </MetadataRow>
        <MetadataRow>
          <MetadataLabel>Subject:</MetadataLabel>
          <MetadataValue>{thread.subject || 'No Subject'}</MetadataValue>
        </MetadataRow>
        
        {/* Participants Section */}
        <ParticipantsSection>
          <ParticipantsTitle>
            <Users size={14} />
            Participants ({participants.length})
          </ParticipantsTitle>
          
          <BadgeContainer>
            {/* Sender Badges */}
            {senderParticipants.map((participant, idx) => (
              <Badge key={`sender-${idx}`} $type="sender" $isCurrentUser={participant.isCurrentUser}>
                <User size={12} />
                {participant.email}
                {participant.isCurrentUser && ' (You)'}
              </Badge>
            ))}
            
            {/* CC Badges */}
            {ccParticipants.map((participant, idx) => (
              <Badge key={`cc-${idx}`} $type="cc" $isCurrentUser={participant.isCurrentUser}>
                <Users size={12} />
                {participant.email}
                {participant.isCurrentUser && ' (You)'}
              </Badge>
            ))}
            
            {/* BCC Badges */}
            {bccParticipants.map((participant, idx) => (
              <Badge key={`bcc-${idx}`} $type="bcc" $isCurrentUser={participant.isCurrentUser}>
                <Users size={12} />
                {participant.email}
                {participant.isCurrentUser && ' (You)'}
              </Badge>
            ))}
            
            {/* Recipient Badges */}
            {recipientParticipants.map((participant, idx) => (
              <Badge key={`recipient-${idx}`} $type="recipient" $isCurrentUser={participant.isCurrentUser}>
                <User size={12} />
                {participant.email}
                {participant.isCurrentUser && ' (You)'}
              </Badge>
            ))}
          </BadgeContainer>
        </ParticipantsSection>
      </MetadataContainer>
    );
  };

  return (
            <ResultsContainer $hasSelectedThreads={selectedThreads.length > 0}>
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
                  <MessageSquare size={14} />
                  {(thread.message_count || thread.mail_count || 1)} emails
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
      {selectedThreads.length > 0 && (
        <StickyProcessContainer>
          <SelectionInfo>
            <Users size={16} />
            <span className="count">{selectedThreads.length}</span>
            {selectedThreads.length === 1 ? 'thread selected' : 'threads selected'}
          </SelectionInfo>
          <ProcessButton onClick={onProcessSelected} disabled={isLoading}>
            {!isLoading && <Sparkles size={18} />}
            {isLoading ? 'Processing...' : `Process Threads (${selectedThreads.length})`}
            {isLoading && <Loader2 size={18} className="animate-spin" />}
          </ProcessButton>
          <ClearButton onClick={() => {
            // Clear all selected threads
            selectedThreads.forEach(id => onThreadToggle(id));
          }} disabled={isLoading}>
            <XCircle size={16} />
            Clear Selection
          </ClearButton>
        </StickyProcessContainer>
      )}
    </ResultsContainer>
  );
}

export default SearchResults;
