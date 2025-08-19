import React, { useState } from 'react';
import styled, { keyframes } from 'styled-components';
import { Search, Mail, FileText, Calendar, User, Filter, Sparkles, AlertCircle } from 'lucide-react';
import axios from 'axios';
import { format } from 'date-fns';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import SearchResults from './components/SearchResults';
import AnalysisReport from './components/AnalysisReport';
import MeetingFlowReport from './components/MeetingFlowReport';
import ClientDossierReport from './components/ClientDossierReport';

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

const slideDown = keyframes`
  from {
    opacity: 0;
    transform: translateY(-10px);
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
    opacity: 0.5;
  }
`;

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background: linear-gradient(135deg, var(--gray-50) 0%, var(--primary-50) 100%);
  color: var(--gray-800);
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

const TopBar = styled.div`
  position: sticky;
  top: 0;
  z-index: 50;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--gray-200);
  padding: var(--space-6) var(--space-8);
  box-shadow: var(--shadow-sm);
  animation: ${slideDown} 0.6s ease-out;
  
  @media (max-width: 768px) {
    padding: var(--space-4) var(--space-5);
  }
`;

const SearchSection = styled.div`
  margin-bottom: var(--space-6);
`;

const SectionHeader = styled.div`
  display: flex;
  align-items: center;
  gap: var(--space-3);
  margin-bottom: var(--space-5);
`;

const SectionTitle = styled.h2`
  font-size: 1.25rem;
  font-weight: 700;
  color: var(--gray-800);
  margin: 0;
`;

const SectionIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  background: var(--primary-500);
  border-radius: var(--radius-lg);
  color: white;
`;

const FiltersRow = styled.div`
  display: grid;
  gap: var(--space-5);
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  align-items: end;
  
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
    gap: var(--space-4);
  }
`;

const FormGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: var(--space-2);
`;

const Label = styled.label`
  display: flex;
  align-items: center;
  gap: var(--space-2);
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--gray-700);
  
  svg {
    width: 16px;
    height: 16px;
    color: var(--gray-500);
  }
`;

const RequiredIndicator = styled.span`
  color: var(--error-500);
  font-weight: 700;
  margin-left: var(--space-1);
`;

const Input = styled.input`
  width: 100%;
  padding: var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  background-color: white;
  color: var(--gray-800);
  font-size: 0.875rem;
  font-family: var(--font-sans);
  transition: all var(--transition-fast);
  
  &:focus {
    outline: none;
    border-color: var(--primary-500);
    box-shadow: 0 0 0 3px var(--primary-100);
  }
  
  &:hover:not(:focus) {
    border-color: var(--gray-400);
  }
  
  &::placeholder {
    color: var(--gray-500);
  }
  
  &.error {
    border-color: var(--error-500);
    background-color: var(--error-50);
    
    &:focus {
      box-shadow: 0 0 0 3px var(--error-100);
    }
  }
`;

const StyledDatePicker = styled(DatePicker)`
  width: 100%;
  padding: var(--space-4);
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-md);
  background-color: white;
  color: var(--gray-800);
  font-size: 0.875rem;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:focus {
    outline: none;
    border-color: var(--primary-500);
    box-shadow: 0 0 0 3px var(--primary-100);
  }
  
  &:hover:not(:focus) {
    border-color: var(--gray-400);
  }
  
  &::placeholder {
    color: var(--gray-500);
  }
`;

const DatePickerContainer = styled.div`
  position: relative;
`;

const QuickDateButtons = styled.div`
  display: flex;
  gap: var(--space-1);
  margin-bottom: var(--space-2);
  flex-wrap: wrap;
`;

const QuickDateButton = styled.button`
  padding: var(--space-1) var(--space-2);
  font-size: 0.75rem;
  font-weight: 500;
  border: 1px solid var(--gray-300);
  border-radius: var(--radius-sm);
  background: white;
  color: var(--gray-700);
  cursor: pointer;
  transition: all var(--transition-fast);
  
  &:hover {
    background: var(--primary-50);
    border-color: var(--primary-300);
    color: var(--primary-700);
  }
  
  &.active {
    background: var(--primary-500);
    border-color: var(--primary-500);
    color: white;
  }
`;

const Button = styled.button`
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.875rem;
  font-weight: 600;
  font-family: var(--font-sans);
  cursor: pointer;
  transition: all var(--transition-fast);
  position: relative;
  overflow: hidden;
  
  &.primary {
    background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
    color: white;
    box-shadow: var(--shadow-md);
    
    &:hover:not(:disabled) {
      background: linear-gradient(135deg, var(--primary-600) 0%, var(--primary-700) 100%);
      box-shadow: var(--shadow-lg);
      transform: translateY(-2px);
    }
    
    &:active {
      transform: translateY(0);
      box-shadow: var(--shadow-md);
    }
  }
  
  &.secondary {
    background: white;
    color: var(--gray-700);
    border: 1px solid var(--gray-300);
    
    &:hover:not(:disabled) {
      background: var(--gray-50);
      border-color: var(--gray-400);
    }
  }
  
  &:disabled {
    background: var(--gray-200) !important;
    color: var(--gray-500) !important;
    cursor: not-allowed;
    transform: none !important;
    box-shadow: none !important;
    border-color: var(--gray-200) !important;
  }
  
  &.loading {
    color: transparent;
    
    &::after {
      content: '';
      position: absolute;
      width: 20px;
      height: 20px;
      border: 2px solid currentColor;
      border-radius: 50%;
      border-top-color: transparent;
      animation: spin 1s linear infinite;
      color: inherit;
    }
  }
  
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
`;

const SearchButton = styled(Button)`
  width: 100%;
  padding: var(--space-5) var(--space-6);
  font-size: 1rem;
  margin-top: var(--space-5);
`;

const MainContent = styled.div`
  flex: 1;
  padding: var(--space-8) var(--space-6);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  overflow-y: auto;
  animation: ${fadeIn} 0.8s ease-out;
  
  @media (max-width: 768px) {
    padding: var(--space-6) var(--space-4);
  }
`;

const HeroSection = styled.div`
  text-align: center;
  margin-bottom: var(--space-12);
  max-width: 900px;
`;

const Title = styled.h1`
  font-size: clamp(2rem, 4vw, 3rem);
  font-weight: 800;
  margin-bottom: var(--space-6);
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-4);
  background: linear-gradient(135deg, var(--gray-800) 0%, var(--primary-600) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
`;

const TitleIcon = styled.div`
  width: 48px;
  height: 48px;
  background: linear-gradient(135deg, var(--primary-500) 0%, var(--primary-600) 100%);
  border-radius: var(--radius-xl);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  box-shadow: var(--shadow-lg);
  animation: ${pulse} 2s ease-in-out infinite;
`;

const Description = styled.p`
  font-size: 1.125rem;
  color: var(--gray-600);
  line-height: 1.7;
  max-width: 600px;
  margin: 0 auto var(--space-8);
`;

const DossierContainer = styled.div`
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-8);
  padding: var(--space-8);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-lg);
  color: var(--gray-800);
  white-space: pre-wrap;
  line-height: 1.6;
  animation: ${fadeIn} 0.6s ease-out;
  
  h3 {
    color: var(--gray-800) !important;
    font-size: 1.25rem;
    font-weight: 700;
    margin-bottom: var(--space-4) !important;
    display: flex;
    align-items: center;
    gap: var(--space-2);
    
    &::before {
      content: '';
      width: 4px;
      height: 20px;
      background: var(--primary-500);
      border-radius: 2px;
    }
  }
`;

const ActionsBar = styled.div`
  position: sticky;
  bottom: 0;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(20px);
  border-top: 1px solid var(--gray-200);
  padding: var(--space-4) var(--space-6);
  display: flex;
  gap: var(--space-3);
  justify-content: center;
  width: 100%;
  box-shadow: var(--shadow-lg);
  z-index: 40;
`;

const Alert = styled.div`
  padding: var(--space-4) var(--space-5);
  border-radius: var(--radius-lg);
  margin-bottom: var(--space-4);
  display: flex;
  align-items: flex-start;
  gap: var(--space-3);
  font-size: 0.875rem;
  line-height: 1.5;
  animation: ${slideDown} 0.4s ease-out;
  
  &.error {
    background-color: var(--error-50);
    border: 1px solid var(--error-200);
    color: var(--error-800);
    
    svg {
      color: var(--error-500);
      flex-shrink: 0;
      margin-top: 2px;
    }
  }
  
  &.warning {
    background-color: var(--warning-50);
    border: 1px solid var(--warning-200);
    color: var(--warning-800);
    
    svg {
      color: var(--warning-500);
      flex-shrink: 0;
      margin-top: 2px;
    }
  }
  
  &.success {
    background-color: var(--success-50);
    border: 1px solid var(--success-200);
    color: var(--success-800);
    
    svg {
      color: var(--success-500);
      flex-shrink: 0;
      margin-top: 2px;
    }
  }
`;

const ButtonGrid = styled.div`
  display: grid;
  gap: var(--space-4);
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-6);
  
  &.full-width {
    .full-width-button {
      grid-column: 1 / -1;
    }
  }
`;

const ClientSelector = styled.div`
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-6);
  padding: var(--space-6);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-md);
  animation: ${fadeIn} 0.6s ease-out;
  
  h4 {
    margin: 0 0 var(--space-4) 0;
    color: var(--gray-800);
    font-size: 1.125rem;
    font-weight: 600;
  }
  
  .client-options {
    display: flex;
    flex-direction: column;
    gap: var(--space-3);
  }
  
  .client-option {
    display: flex;
    align-items: center;
    gap: var(--space-3);
    padding: var(--space-3) var(--space-4);
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-fast);
    border: 1px solid var(--gray-200);
    
    &:hover {
      background: var(--gray-50);
      border-color: var(--gray-300);
    }
    
    &.selected {
      background: var(--primary-50);
      border-color: var(--primary-200);
      
      .client-name {
        color: var(--primary-800);
        font-weight: 600;
      }
    }
    
    input[type="radio"] {
      margin: 0;
      accent-color: var(--primary-500);
    }
    
    .client-name {
      font-size: 0.875rem;
      color: var(--gray-700);
      transition: all var(--transition-fast);
    }
  }
  
  .selected-info {
    margin-top: var(--space-4);
    padding: var(--space-3);
    background: var(--primary-50);
    border-radius: var(--radius-md);
    font-size: 0.75rem;
    color: var(--primary-700);
    font-style: italic;
  }
`;

const TabbedDossierContainer = styled.div`
  width: 100%;
  max-width: 900px;
  margin-top: var(--space-8);
  background: white;
  border-radius: var(--radius-xl);
  border: 1px solid var(--gray-200);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  animation: ${fadeIn} 0.6s ease-out;
`;

const TabNavigation = styled.div`
  display: flex;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  overflow-x: auto;
  
  &::-webkit-scrollbar {
    height: 4px;
  }
  
  &::-webkit-scrollbar-track {
    background: var(--gray-100);
  }
  
  &::-webkit-scrollbar-thumb {
    background: var(--gray-300);
    border-radius: 2px;
  }
`;

const TabButton = styled.button`
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-4) var(--space-6);
  background: transparent;
  border: none;
  color: var(--gray-600);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-fast);
  white-space: nowrap;
  border-bottom: 3px solid transparent;
  
  &:hover {
    background: var(--gray-100);
    color: var(--gray-800);
  }
  
  &.active {
    background: white;
    color: var(--primary-600);
    border-bottom-color: var(--primary-500);
    font-weight: 600;
  }
  
  svg {
    flex-shrink: 0;
  }
`;

const TabContent = styled.div`
  padding: 0;
  
  /* Override the margin-top from AnalysisReport since it's now inside a tab */
  & > * {
    margin-top: 0 !important;
  }
`;

function App() {
  const [isMenuOpen, setIsMenuOpen] = useState(true);
  const [startDate, setStartDate] = useState(new Date(2023, 0, 1));
  const [endDate, setEndDate] = useState(new Date(2025, 7, 5));
  const [activeStartDateRange, setActiveStartDateRange] = useState('');
  const [activeEndDateRange, setActiveEndDateRange] = useState('');
  const [keyword, setKeyword] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [advancedQuery, setAdvancedQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedThreads, setSelectedThreads] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [processedMetadata, setProcessedMetadata] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [keywordError, setKeywordError] = useState(false);

  const [dossier, setDossier] = useState(null);
  const [meetingDossier, setMeetingDossier] = useState(null);
  const [clientDossier, setClientDossier] = useState(null);
  const [isGeneratingMeeting, setIsGeneratingMeeting] = useState(false);
  const [isGeneratingClient, setIsGeneratingClient] = useState(false);
  const [clientValidation, setClientValidation] = useState({ valid: false, client_name: '', reason: '' });
  const [selectedClientName, setSelectedClientName] = useState('');
  const [availableClientNames, setAvailableClientNames] = useState([]);
  const [activeDossierTab, setActiveDossierTab] = useState('agenda');

  const handleSearch = async () => {
    setIsLoading(true);
    setError('');
    setWarning('');
    setSearchResults([]);
    setSelectedThreads([]);
    setProcessedMetadata(null);
    setAnalysisResults(null);
    setDossier(null);
    setKeywordError(false);
    setMeetingDossier(null);

    setClientDossier(null);
    setClientValidation({ valid: false, client_name: '', reason: '' });
    setSelectedClientName('');
    setAvailableClientNames([]);

    // Make keyword compulsory
    if (!keyword.trim()) {
      setError('Keyword is required.');
      setKeywordError(true);
      setIsLoading(false);
      return;
    }

    // Validate dates
    if (startDate > endDate) {
      setError('Start date cannot be after end date.');
      setIsLoading(false);
      return;
    }
    
    // Check if at least one search parameter is provided
    const hasSearchCriteria = keyword || senderEmail;
    if (!hasSearchCriteria) {
      setWarning('No search criteria provided. Searching all emails in the date range...');
    }
    
    try {
      const response = await axios.post('/api/find_threads', {
        start_date: format(startDate, 'yyyy/MM/dd'),
        end_date: format(endDate, 'yyyy/MM/dd'),
        keyword: keyword || null,
        from_email: senderEmail || null,
        query: advancedQuery || null
      });
      
      setSearchResults(response.data);
      if (response.data.length === 0) {
        setWarning('No relevant email threads found. Try adjusting your search criteria.');
      } else {
        setWarning(`Found ${response.data.length} email threads.`);
      }
    } catch (error) {
      console.error('Error searching emails:', error);
      setError('An error occurred while finding emails. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleThreadToggle = (threadId) => {
    setSelectedThreads(prev => 
      prev.includes(threadId)
        ? prev.filter(id => id !== threadId)
        : [...prev, threadId]
    );
  };

  const handleProcessThreads = async () => {
    if (selectedThreads.length === 0) return;
    
    setIsProcessing(true);
    setError('');
    setProcessedMetadata(null);
    setAnalysisResults(null);
    
    try {
      const response = await axios.post('/api/process_threads_metadata', {
        thread_ids: selectedThreads
      });
      
      setProcessedMetadata(response.data);
      
      // Debug logging
      console.log('Processed metadata:', response.data);
      console.log('Available client names:', response.data.available_client_names);
      
      const clientNamesFound = response.data.available_client_names && 
        response.data.available_client_names.length > 0 && 
        response.data.available_client_names[0] !== 'Unknown Client';
      
      if (clientNamesFound) {
        setWarning(`Processed ${selectedThreads.length} threads. Found client: ${response.data.available_client_names[0]}. Ready for generation.`);
      } else {
        setWarning(`Processed ${selectedThreads.length} threads. No external client detected. Analysis may help identify client.`);
      }
    } catch (error) {
      console.error('Error processing threads:', error);
      setError('An error occurred while processing threads. Please try again.');
    } finally {
      setIsProcessing(false);
    }
  };

  const handleGenerateTillDateAgenda = async () => {
    if (!processedMetadata) return;
    
    setIsAnalyzing(true);
    setError('');
    setAnalysisResults(null);
    
    try {
      // If we already have analysis results, use them, otherwise generate new analysis
      let analysisData;
      if (analysisResults) {
        analysisData = analysisResults;
      } else {
        // Generate analysis from processed metadata
        const response = await axios.post('/api/analyze_multiple_threads', {
          thread_ids: processedMetadata.processed_thread_ids
        });
        analysisData = response.data;
        setAnalysisResults(analysisData);
      }
      
      setActiveDossierTab('agenda'); // Auto-switch to agenda tab
      setWarning('Till Date Agenda generated successfully.');
    } catch (error) {
      console.error('Error generating till date agenda:', error);
      setError('An error occurred while generating till date agenda. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateMeetingFlow = async () => {
    if (!processedMetadata) return;
    
    setIsGeneratingMeeting(true);
    setError('');
    
    try {
      // If we don't have analysis results, generate them first
      let analysisData = analysisResults;
      if (!analysisData) {
        const analysisResponse = await axios.post('/api/analyze_multiple_threads', {
          thread_ids: processedMetadata.processed_thread_ids
        });
        analysisData = analysisResponse.data;
        setAnalysisResults(analysisData);
      }
      
      // Generate meeting flow using analysis data
      const response = await axios.post('/api/generate_meeting_dossier', {
        analysis: analysisData
      });
      
      setMeetingDossier(response.data || null);
      setActiveDossierTab('meeting'); // Auto-switch to meeting tab
      setWarning('Meeting Flow Dossier generated successfully.');
    } catch (error) {
      console.error('Error generating meeting flow:', error);
      setError('An error occurred while generating meeting flow. Please try again.');
    } finally {
      setIsGeneratingMeeting(false);
    }
  };

  const handleGenerateClientDossierFromMetadata = async () => {
    if (!processedMetadata) return;
    
    // Try multiple sources for client name
    let clientName = 'Unknown Client';
    
    // 1. Check if we have analysis results with structured client name
    if (analysisResults && analysisResults.structured_analysis && analysisResults.structured_analysis.client_name) {
      const analysisClientName = analysisResults.structured_analysis.client_name;
      if (analysisClientName && analysisClientName.toLowerCase() !== 'unknown client') {
        clientName = analysisClientName;
      }
    }
    
    // 2. Fallback to metadata available client names
    if (clientName === 'Unknown Client' && processedMetadata.available_client_names && processedMetadata.available_client_names.length > 0) {
      const metadataClientName = processedMetadata.available_client_names[0];
      if (metadataClientName && metadataClientName.toLowerCase() !== 'unknown client') {
        clientName = metadataClientName;
      }
    }
    
    if (clientName === 'Unknown Client') {
      setError('No client name found in the processed threads. Cannot generate client dossier.');
      return;
    }
    
    setIsGeneratingClient(true);
    setError('');
    
    try {
      const response = await axios.post('/api/generate_client_dossier', {
        client_name: clientName,
        client_domain: '',
        client_context: ''
      });
      
      setClientDossier(response.data || null);
      setActiveDossierTab('client'); // Auto-switch to client tab
      setWarning(`Client Dossier for ${clientName} generated successfully.`);
    } catch (error) {
      console.error('Error generating client dossier:', error);
      setError('An error occurred while generating client dossier. Please try again.');
    } finally {
      setIsGeneratingClient(false);
    }
  };

  const handleAnalyzeSelected = async () => {
    if (selectedThreads.length === 0) return;
    
    setIsAnalyzing(true);
    setAnalysisResults(null);
    setDossier(null);
    
    try {
      let response;
      if (selectedThreads.length === 1) {
        response = await axios.post('/api/analyze_thread', {
          thread_id: selectedThreads[0]
        });
      } else {
        response = await axios.post('/api/analyze_multiple_threads', {
          thread_ids: selectedThreads
        });
      }
      
      setAnalysisResults(response.data);
      
      // Handle available client names from domain extraction
      if (response.data.available_client_names && response.data.available_client_names.length > 0) {
        setAvailableClientNames(response.data.available_client_names);
        // Auto-select the first client name if only one is available
        if (response.data.available_client_names.length === 1) {
          setSelectedClientName(response.data.available_client_names[0]);
        } else {
          setSelectedClientName(''); // Let user choose if multiple
        }
      } else {
        setAvailableClientNames([]);
        setSelectedClientName('');
      }
      
      // Validate client name for dossier generation
      await validateClientName(response.data);
    } catch (error) {
      console.error('Error analyzing threads:', error);
      setError('An error occurred during analysis. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };


  

  
  const validateClientName = async (analysisData) => {
    try {
      const response = await axios.post('/api/validate_client_name', {
        analysis: {
          structured_analysis: analysisData.structured_analysis,
          analysis: analysisData.analysis
        }
      });
      setClientValidation(response.data);
    } catch (error) {
      console.error('Error validating client name:', error);
      setClientValidation({ valid: false, client_name: '', reason: 'Error validating client name' });
    }
  };

  const handleGenerateClientDossier = async () => {
    // Use selected client name if available, otherwise fall back to validated client name
    const clientNameToUse = selectedClientName || clientValidation.client_name;
    
    if (!clientNameToUse) {
      setError('Please select a client name from the available options.');
      return;
    }
    
    setIsGeneratingClient(true);
    setError('');
    try {
      const response = await axios.post('/api/generate_client_dossier', {
        client_name: clientNameToUse,
        client_domain: '',
        client_context: ''
      });
      setClientDossier(response.data || null);
    } catch (e) {
      console.error('Error generating client dossier:', e);
      setError('An error occurred while generating the client dossier.');
    } finally {
      setIsGeneratingClient(false);
    }
  };
  




  return (
    <AppContainer>
      <TopBar>
        <SearchSection>
          <SectionHeader>
            <SectionIcon>
              <Mail size={18} />
            </SectionIcon>
            <SectionTitle>Search Emails</SectionTitle>
          </SectionHeader>
          
          <FiltersRow>
            <FormGroup>
              <Label>
                <Calendar size={16} />
                Start Date
              </Label>
              <StyledDatePicker
                selected={startDate}
                onChange={(date) => setStartDate(date)}
                dateFormat="yyyy/MM/dd"
                placeholderText="Select start date"
                maxDate={endDate}
                showYearDropdown
                scrollableYearDropdown
                yearDropdownItemNumber={15}
                showMonthDropdown
                scrollableMonthDropdown
                showMonthYearPicker={false}
                showFullMonthYearPicker={false}
              />
            </FormGroup>
            
            <FormGroup>
              <Label>
                <Calendar size={16} />
                End Date
              </Label>
              <StyledDatePicker
                selected={endDate}
                onChange={(date) => setEndDate(date)}
                dateFormat="yyyy/MM/dd"
                placeholderText="Select end date"
                minDate={startDate}
                showYearDropdown
                scrollableYearDropdown
                yearDropdownItemNumber={15}
                showMonthDropdown
                scrollableMonthDropdown
                showMonthYearPicker={false}
                showFullMonthYearPicker={false}
              />
            </FormGroup>
            
            <FormGroup>
              <Label>
                <Search size={16} />
                Keyword
                <RequiredIndicator>*</RequiredIndicator>
              </Label>
              <Input
                type="text"
                value={keyword}
                onChange={(e) => { setKeyword(e.target.value); setKeywordError(false); }}
                placeholder="e.g., invoice, roadmap, meeting"
                className={keywordError ? 'error' : ''}
                required
              />
            </FormGroup>
            
            <FormGroup>
              <Label>
                <User size={16} />
                Sender Email
              </Label>
              <Input
                type="email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
                placeholder="someone@company.com"
              />
            </FormGroup>
            
            <FormGroup>
              <Label>
                <Filter size={16} />
                Advanced Query
              </Label>
              <Input
                type="text"
                value={advancedQuery}
                onChange={(e) => setAdvancedQuery(e.target.value)}
                placeholder='subject:"invoice" has:attachment'
              />
            </FormGroup>
          </FiltersRow>
          
          <SearchButton 
            className={`primary ${isLoading ? 'loading' : ''}`}
            onClick={handleSearch} 
            disabled={isLoading}
          >
            {!isLoading && <Search size={20} />}
            {isLoading ? 'Searching...' : 'Find Relevant Emails'}
          </SearchButton>
        </SearchSection>
      </TopBar>
      
      <MainContent>
        <HeroSection>
          <Title>
            <TitleIcon>
              <Sparkles />
            </TitleIcon>
            Email Thread Analyzer
          </Title>
          
          <Description>
            Transform your email conversations into actionable insights. Search, analyze, and generate comprehensive dossiers from your email threads with AI-powered intelligence.
          </Description>
        </HeroSection>
        
        {error && (
          <Alert className="error">
            <AlertCircle size={18} />
            <div>{error}</div>
          </Alert>
        )}
        
        {warning && (
          <Alert className="warning">
            <AlertCircle size={18} />
            <div>{warning}</div>
          </Alert>
        )}

        {searchResults.length > 0 && (
          <SearchResults
            results={searchResults}
            selectedThreads={selectedThreads}
            onThreadToggle={handleThreadToggle}
            onProcessSelected={handleProcessThreads}
            isLoading={isProcessing}
          />
        )}

        {/* Tabbed Dossier Display */}
        {(analysisResults || meetingDossier || clientDossier || dossier) && (
          <TabbedDossierContainer>
            <TabNavigation>
        {analysisResults && (
                <TabButton 
                  className={activeDossierTab === 'agenda' ? 'active' : ''}
                  onClick={() => setActiveDossierTab('agenda')}
                >
                  <FileText size={16} />
                  Till Date Agenda
                </TabButton>
              )}
              {meetingDossier && (
                <TabButton 
                  className={activeDossierTab === 'meeting' ? 'active' : ''}
                  onClick={() => setActiveDossierTab('meeting')}
                >
                  <Calendar size={16} />
                  Meeting Flow Dossier
                </TabButton>
              )}
              {clientDossier && (
                <TabButton 
                  className={activeDossierTab === 'client' ? 'active' : ''}
                  onClick={() => setActiveDossierTab('client')}
                >
                  <User size={16} />
                  Client Dossier
                </TabButton>
              )}
              {dossier && (
                <TabButton 
                  className={activeDossierTab === 'legacy' ? 'active' : ''}
                  onClick={() => setActiveDossierTab('legacy')}
                >
                  <FileText size={16} />
                  Legacy Dossier
                </TabButton>
              )}
            </TabNavigation>

            <TabContent>
              {activeDossierTab === 'agenda' && analysisResults && (
          <AnalysisReport
            structuredAnalysis={analysisResults.structured_analysis}
            rawAnalysis={analysisResults.analysis}
                  threadMetadata={analysisResults.thread_metadata || processedMetadata?.combined_metadata}
                  combinedMetadata={analysisResults.combined_metadata || processedMetadata?.combined_metadata}
                  productName={
                    (analysisResults.product_name && analysisResults.product_name !== 'Unknown Product') 
                      ? analysisResults.product_name 
                      : (processedMetadata?.product_name !== 'Unknown Product' ? processedMetadata?.product_name : null)
                  }
                  productDomain={
                    (analysisResults.product_domain && analysisResults.product_domain !== 'general product') 
                      ? analysisResults.product_domain 
                      : (processedMetadata?.product_domain !== 'general product' ? processedMetadata?.product_domain : null)
                  }
                />
              )}

              {activeDossierTab === 'meeting' && meetingDossier && (
                <MeetingFlowReport meetingFlowData={meetingDossier} />
              )}

              {activeDossierTab === 'client' && clientDossier && (
                <ClientDossierReport clientDossierData={clientDossier} />
              )}

              {activeDossierTab === 'legacy' && dossier && (
                <DossierContainer>
                  <div>
                    <h4 style={{ color: 'var(--gray-800)', marginBottom: 'var(--space-2)' }}>Meeting Flow</h4>
                    <div style={{ marginBottom: 'var(--space-4)' }}>
                      {dossier.meeting_flow || ''}
                    </div>
                    <h4 style={{ color: 'var(--gray-800)', marginBottom: 'var(--space-2)' }}>Client Details</h4>
                    <div>
                      {dossier.client_details || 'Client Details: To be added.'}
                    </div>
                  </div>
                </DossierContainer>
              )}
            </TabContent>
          </TabbedDossierContainer>
        )}

        {/* Client Name Selection */}
        {analysisResults && availableClientNames.length > 1 && (
          <ClientSelector>
            <h4>Multiple Client Names Found - Please Select One:</h4>
            <div className="client-options">
              {availableClientNames.map((clientName, index) => (
                <label 
                  key={index} 
                  className={`client-option ${selectedClientName === clientName ? 'selected' : ''}`}
                >
                  <input
                    type="radio"
                    name="clientName"
                    value={clientName}
                    checked={selectedClientName === clientName}
                    onChange={(e) => setSelectedClientName(e.target.value)}
                  />
                  <span className="client-name">{clientName}</span>
                </label>
              ))}
            </div>
            {selectedClientName && (
              <div className="selected-info">
                Selected: <strong>{selectedClientName}</strong>
              </div>
            )}
          </ClientSelector>
        )}




        {selectedThreads.length > 0 && !processedMetadata && (
          <ActionsBar>
            <Button 
              className={`primary ${isProcessing ? 'loading' : ''}`}
              onClick={handleProcessThreads} 
              disabled={isProcessing}
            >
              {!isProcessing && <Sparkles size={18} />}
              {isProcessing ? 'Processing...' : `Process Threads (${selectedThreads.length})`}
            </Button>
            <Button 
              className="secondary"
              onClick={() => setSelectedThreads([])} 
              disabled={isProcessing}
            >
              Clear Selection
            </Button>
          </ActionsBar>
        )}

        {/* Three Option Buttons - Show after processing */}
        {processedMetadata && (
          <ButtonGrid className="full-width">
            <Button 
              className={`primary ${isAnalyzing ? 'loading' : ''}`}
              onClick={handleGenerateTillDateAgenda} 
              disabled={isAnalyzing || isGeneratingMeeting || isGeneratingClient}
            >
              {!isAnalyzing && <FileText size={18} />}
              {isAnalyzing ? 'Generating...' : '1. Till Date Agenda'}
            </Button>
            
            <Button 
              className={`primary ${isGeneratingMeeting ? 'loading' : ''}`}
              onClick={handleGenerateMeetingFlow} 
              disabled={isGeneratingMeeting || isAnalyzing || isGeneratingClient}
            >
              {!isGeneratingMeeting && <Calendar size={18} />}
              {isGeneratingMeeting ? 'Generating...' : '2. Meeting Flow Dossier'}
            </Button>
            
            <Button 
              className={`primary ${isGeneratingClient ? 'loading' : ''}`}
              onClick={handleGenerateClientDossierFromMetadata} 
              disabled={(() => {
                // Always disabled during operations
                if (isGeneratingClient || isAnalyzing || isGeneratingMeeting) {
                  return true;
                }
                
                // Check if we have a valid client name from either source
                let hasValidClient = false;
                
                // Check analysis results first (most reliable)
                if (analysisResults && analysisResults.structured_analysis && analysisResults.structured_analysis.client_name) {
                  const analysisClientName = analysisResults.structured_analysis.client_name;
                  if (analysisClientName && analysisClientName.toLowerCase() !== 'unknown client') {
                    hasValidClient = true;
                  }
                }
                
                // Check metadata if no analysis client found
                if (!hasValidClient && processedMetadata && processedMetadata.available_client_names) {
                  const metadataClientNames = processedMetadata.available_client_names;
                  if (metadataClientNames.length > 0 && metadataClientNames[0].toLowerCase() !== 'unknown client') {
                    hasValidClient = true;
                  }
                }
                
                return !hasValidClient;
              })()}
              title={(() => {
                // Get available client name for display
                let availableClientName = null;
                
                // First check analysis results (most reliable after analysis is done)
                if (analysisResults && analysisResults.structured_analysis && analysisResults.structured_analysis.client_name) {
                  const analysisClientName = analysisResults.structured_analysis.client_name;
                  if (analysisClientName && analysisClientName.toLowerCase() !== 'unknown client') {
                    availableClientName = analysisClientName;
                  }
                }
                
                // Fallback to metadata (available after processing but less reliable)
                if (!availableClientName && processedMetadata.available_client_names && processedMetadata.available_client_names.length > 0) {
                  const metadataClientName = processedMetadata.available_client_names[0];
                  if (metadataClientName && metadataClientName.toLowerCase() !== 'unknown client') {
                    availableClientName = metadataClientName;
                  }
                }
                
                if (availableClientName) {
                  return `Generate dossier for ${availableClientName}`;
                } else if (analysisResults) {
                  return 'No client name found in analysis';
                } else {
                  return 'Generate analysis first to identify client';
                }
              })()}
            >
              {!isGeneratingClient && <User size={18} />}
              {isGeneratingClient ? 'Generating...' : (() => {
                // Get available client name for button text
                let availableClientName = null;
                
                // First check analysis results (most reliable after analysis is done)
                if (analysisResults && analysisResults.structured_analysis && analysisResults.structured_analysis.client_name) {
                  const analysisClientName = analysisResults.structured_analysis.client_name;
                  if (analysisClientName && analysisClientName.toLowerCase() !== 'unknown client') {
                    availableClientName = analysisClientName;
                  }
                }
                
                // Fallback to metadata (available after processing but less reliable)
                if (!availableClientName && processedMetadata.available_client_names && processedMetadata.available_client_names.length > 0) {
                  const metadataClientName = processedMetadata.available_client_names[0];
                  if (metadataClientName && metadataClientName.toLowerCase() !== 'unknown client') {
                    availableClientName = metadataClientName;
                  }
                }
                
                if (availableClientName) {
                  return `3. Client Dossier (${availableClientName})`;
                } else if (analysisResults) {
                  return '3. Client Dossier (No Client Found)';
                } else {
                  return '3. Client Dossier (Generate Analysis First)';
                }
              })()}
            </Button>
            
            <Button 
              className="secondary"
              onClick={() => {
                setProcessedMetadata(null);
                setSelectedThreads([]);
                setAnalysisResults(null);
                setMeetingDossier(null);
                setClientDossier(null);
                setActiveDossierTab('agenda'); // Reset to default tab
              }}
              disabled={isAnalyzing || isGeneratingMeeting || isGeneratingClient}
            >
              Start Over
            </Button>
          </ButtonGrid>
        )}
      </MainContent>
    </AppContainer>
  );
}

export default App;