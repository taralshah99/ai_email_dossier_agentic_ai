import React from 'react';
import styled from 'styled-components';
import { User, Mail, LogOut, Shield } from 'lucide-react';

const ProfileContainer = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3) var(--space-4);
  background: white;
  border-radius: var(--radius-lg);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-sm);
`;

const Avatar = styled.div`
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 0.875rem;
  
  svg {
    width: 20px;
    height: 20px;
  }
`;

const UserInfo = styled.div`
  flex: 1;
  min-width: 0;
`;

const UserEmail = styled.div`
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-800);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
`;

const UserStats = styled.div`
  font-size: 0.75rem;
  color: var(--gray-500);
  display: flex;
  align-items: center;
  gap: var(--space-2);
  
  svg {
    width: 12px;
    height: 12px;
  }
`;

const LogoutButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: transparent;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  color: var(--gray-600);
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:hover {
    background: var(--error-50);
    border-color: var(--error-200);
    color: var(--error-600);
  }
  
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
`;

const UserProfile = ({ user, onLogout, isLoggingOut = false }) => {
  const getInitials = (email) => {
    if (!email) return 'U';
    const parts = email.split('@')[0].split('.');
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase();
    }
    return email[0].toUpperCase();
  };

  const formatStats = (user) => {
    const messages = user.messages_total || 0;
    const threads = user.threads_total || 0;
    
    if (messages > 0) {
      return `${messages.toLocaleString()} messages`;
    }
    if (threads > 0) {
      return `${threads.toLocaleString()} threads`;
    }
    return 'Gmail connected';
  };

  return (
    <ProfileContainer>
      <Avatar title={`Logged in as ${user.email || 'Unknown'}`}>
        {user.email ? getInitials(user.email) : <User />}
      </Avatar>
      
      <UserInfo>
        <UserEmail title={user.email}>
          {user.email || 'Unknown User'}
        </UserEmail>
        <UserStats>
          <Shield />
          {formatStats(user)}
        </UserStats>
      </UserInfo>
      
      <LogoutButton
        onClick={onLogout}
        disabled={isLoggingOut}
        title="Sign out"
      >
        <LogOut />
      </LogoutButton>
    </ProfileContainer>
  );
};

export default UserProfile;
