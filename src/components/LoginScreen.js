import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { Mail, Sparkles, Shield, Zap } from 'lucide-react';
import axios from 'axios';
import ConsentScreen from './ConsentScreen';

// Animations
const fadeIn = keyframes`
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
`;

const pulse = keyframes`
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
`;

const LoginContainer = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--gray-50) 0%, var(--primary-50) 100%);
  padding: var(--space-8);
  position: relative;
  
  &::before {
    content: '';
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: 
      radial-gradient(circle at 20% 80%, var(--primary-100) 0%, transparent 50%),
      radial-gradient(circle at 80% 20%, var(--primary-100) 0%, transparent 50%);
    pointer-events: none;
    z-index: -1;
  }
`;

const LoginCard = styled.div`
  background: white;
  border-radius: var(--radius-xl);
  padding: var(--space-12);
  box-shadow: var(--shadow-xl);
  border: 1px solid var(--gray-200);
  max-width: 480px;
  width: 100%;
  text-align: center;
  animation: ${fadeIn} 0.8s ease-out;
  
  @media (max-width: 768px) {
    padding: var(--space-8);
    margin: var(--space-4);
  }
`;

const AppIcon = styled.div`
  width: 80px;
  height: 80px;
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto var(--space-6);
  box-shadow: var(--shadow-lg);
  animation: ${pulse} 2s ease-in-out infinite;
  
  svg {
    width: 40px;
    height: 40px;
    color: white;
  }
`;

const Title = styled.h1`
  font-size: 2.5rem;
  font-weight: 800;
  margin-bottom: var(--space-4);
  background: linear-gradient(135deg, var(--gray-800) 0%, var(--primary-600) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const Subtitle = styled.p`
  font-size: 1.125rem;
  color: var(--gray-600);
  margin-bottom: var(--space-8);
  line-height: 1.6;
`;

const LoginButton = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-3);
  width: 100%;
  padding: var(--space-5) var(--space-6);
  background: linear-gradient(135deg, #4285f4 0%, #34a853 50%, #ea4335 100%);
  color: white;
  border: none;
  border-radius: var(--radius-lg);
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all var(--transition-fast);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
  
  &:hover:not(:disabled) {
    transform: translateY(-2px);
    box-shadow: var(--shadow-xl);
  }
  
  &:active {
    transform: translateY(0);
  }
  
  &:disabled {
    background: var(--gray-300);
    color: var(--gray-500);
    cursor: not-allowed;
    transform: none;
  }
  
  &.loading {
    color: transparent;
    
    &::after {
      content: '';
      position: absolute;
      width: 20px;
      height: 20px;
      border: 2px solid white;
      border-radius: 50%;
      border-top-color: transparent;
      animation: spin 1s linear infinite;
    }
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const Features = styled.div`
  margin-top: var(--space-8);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--space-6);
`;

const Feature = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-2);
  
  svg {
    width: 24px;
    height: 24px;
    color: var(--primary-500);
  }
  
  span {
    font-size: 0.875rem;
    color: var(--gray-600);
    font-weight: 500;
  }
`;

const ErrorMessage = styled.div`
  margin-top: var(--space-4);
  padding: var(--space-3) var(--space-4);
  background: var(--error-50);
  border: 1px solid var(--error-200);
  border-radius: var(--radius-md);
  color: var(--error-800);
  font-size: 0.875rem;
  text-align: left;
`;

const LoginScreen = ({ onLoginSuccess }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showConsent, setShowConsent] = useState(false);

  const handleLogin = async () => {
    setIsLoading(true);
    setError('');

    try {
      console.log('Initiating login...');
      // Request login URL from backend
      const response = await axios.post('/api/auth/login');
      console.log('Login response:', response.data);
      const { auth_url } = response.data;

      console.log('Redirecting to:', auth_url);
      // Redirect to Google OAuth
      window.location.href = auth_url;
    } catch (err) {
      console.error('Login error:', err);
      console.error('Error details:', err.response);
      setError(
        err.response?.data?.error || 
        'Failed to initiate login. Please try again.'
      );
      setIsLoading(false);
    }
  };

  const handleConsentAccept = () => {
    setShowConsent(false);
    handleLogin();
  };

  const handleConsentDecline = () => {
    setShowConsent(false);
    setError('');
  };

  if (showConsent) {
    return (
      <LoginContainer>
        <ConsentScreen 
          onAccept={handleConsentAccept}
          onDecline={handleConsentDecline}
        />
      </LoginContainer>
    );
  }

  return (
    <LoginContainer>
      <LoginCard>
        <AppIcon>
          <Sparkles />
        </AppIcon>
        
        <Title>Email Dossier</Title>
        <Subtitle>
          Transform your email conversations into actionable insights with AI-powered analysis.
        </Subtitle>

        <LoginButton 
          onClick={() => setShowConsent(true)} 
          disabled={isLoading}
          className={isLoading ? 'loading' : ''}
          title="Review permissions and sign in with your Google account"
        >
          {!isLoading && <Mail size={20} />}
          {isLoading ? 'Connecting...' : 'Continue with Gmail'}
        </LoginButton>

        {error && (
          <ErrorMessage>
            {error}
          </ErrorMessage>
        )}

        <Features>
          <Feature>
            <Shield />
            <span>Secure OAuth</span>
          </Feature>
          <Feature>
            <Mail />
            <span>Gmail Integration</span>
          </Feature>
          <Feature>
            <Zap />
            <span>AI Analysis</span>
          </Feature>
        </Features>
      </LoginCard>
    </LoginContainer>
  );
};

export default LoginScreen;
