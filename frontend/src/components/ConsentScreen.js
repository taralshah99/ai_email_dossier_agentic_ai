import React, { useState } from 'react';
import styled from 'styled-components';
import { Shield, Mail, Eye, AlertTriangle, Check, X } from 'lucide-react';

const ConsentContainer = styled.div`
  max-width: 500px;
  margin: 0 auto;
  padding: var(--space-8);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-lg);
`;

const ConsentHeader = styled.div`
  text-align: center;
  margin-bottom: var(--space-6);
`;

const ConsentIcon = styled.div`
  width: 64px;
  height: 64px;
  background: var(--warning-100);
  border-radius: var(--radius-full);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-4);
  
  svg {
    width: 32px;
    height: 32px;
    color: var(--warning-600);
  }
`;

const ConsentTitle = styled.h2`
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gray-800);
  margin: 0 0 var(--space-2) 0;
`;

const ConsentSubtitle = styled.p`
  color: var(--gray-600);
  font-size: 0.875rem;
`;

const PermissionsList = styled.div`
  margin: var(--space-6) 0;
  padding: var(--space-4);
  background: var(--gray-50);
  border-radius: var(--radius-lg);
  border-left: 4px solid var(--primary-500);
`;

const PermissionsTitle = styled.h3`
  font-size: 1rem;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0 0 var(--space-3) 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
  
  svg {
    width: 18px;
    height: 18px;
    color: var(--primary-500);
  }
`;

const Permission = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-2) 0;
  font-size: 0.875rem;
  color: var(--gray-700);
  
  svg {
    width: 16px;
    height: 16px;
    color: var(--gray-500);
    flex-shrink: 0;
  }
`;

const SecurityNote = styled.div`
  padding: var(--space-4);
  background: var(--success-50);
  border: 1px solid var(--success-200);
  border-radius: var(--radius-lg);
  margin: var(--space-4) 0;
  
  h4 {
    font-size: 0.875rem;
    font-weight: 600;
    color: var(--success-800);
    margin: 0 0 var(--space-2) 0;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    
    svg {
      width: 16px;
      height: 16px;
    }
  }
  
  p {
    font-size: 0.75rem;
    color: var(--success-700);
    margin: 0;
    line-height: 1.4;
  }
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: var(--space-3);
  margin-top: var(--space-6);
`;

const Button = styled.button`
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  border-radius: var(--radius-lg);
  font-size: 0.875rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &.primary {
    background: var(--primary-500);
    color: white;
    border: 1px solid var(--primary-500);
    
    &:hover {
      background: var(--primary-600);
      transform: translateY(-1px);
    }
  }
  
  &.secondary {
    background: white;
    color: var(--gray-700);
    border: 1px solid var(--gray-300);
    
    &:hover {
      background: var(--gray-50);
    }
  }
  
  svg {
    width: 16px;
    height: 16px;
  }
`;

const ConsentScreen = ({ onAccept, onDecline }) => {
  const [understood, setUnderstood] = useState(false);

  return (
    <ConsentContainer>
      <ConsentHeader>
        <ConsentIcon>
          <Shield />
        </ConsentIcon>
        <ConsentTitle>Permission Required</ConsentTitle>
        <ConsentSubtitle>
          Email Dossier needs access to your Gmail account to analyze your email threads
        </ConsentSubtitle>
      </ConsentHeader>

      <PermissionsList>
        <PermissionsTitle>
          <Mail />
          This application will be able to:
        </PermissionsTitle>
        
        <Permission>
          <Eye />
          Read your Gmail messages and threads
        </Permission>
        
        <Permission>
          <Eye />
          View email metadata (sender, subject, date)
        </Permission>
        
        <Permission>
          <Eye />
          Access your Gmail account information
        </Permission>
      </PermissionsList>

      <SecurityNote>
        <h4>
          <Shield />
          Security & Privacy
        </h4>
        <p>
          • Your emails are processed locally and never stored permanently<br/>
          • Only read-only access is requested - we cannot send emails<br/>
          • You can revoke access anytime in your Google Account settings<br/>
          • All data is deleted when you stop the application
        </p>
      </SecurityNote>

      <ButtonGroup>
        <Button 
          className="secondary" 
          onClick={onDecline}
          title="Cancel and return to login screen"
        >
          <X />
          Cancel
        </Button>
        
        <Button 
          className="primary" 
          onClick={onAccept}
          title="Proceed to Google OAuth consent"
        >
          <Check />
          Continue to Google
        </Button>
      </ButtonGroup>
    </ConsentContainer>
  );
};

export default ConsentScreen;
