import React, { useState } from 'react';
import styled from 'styled-components';
import { Search, Menu, X, Mail, FileText } from 'lucide-react';
import axios from 'axios';
import { format } from 'date-fns';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import SearchResults from './components/SearchResults';
import AnalysisReport from './components/AnalysisReport';

const AppContainer = styled.div`
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #1a1a1a;
  color: #ffffff;
`;

const TopBar = styled.div`
  position: sticky;
  top: 0;
  z-index: 10;
  background: linear-gradient(180deg, #2a2a2a 0%, #262626 100%);
  border-bottom: 1px solid #404040;
  padding: 16px 24px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
`;

const FiltersRow = styled.div`
  display: grid;
  gap: 12px;
  grid-template-columns: 1fr 1fr 1fr 1fr 1.5fr;
  align-items: end;
  
  @media (max-width: 1200px) {
    grid-template-columns: 1fr 1fr 1fr;
  }
  @media (max-width: 768px) {
    grid-template-columns: 1fr;
  }
`;

const BarSection = styled.div``;

const Section = styled.div`
  margin-bottom: 30px;
`;

const SectionTitle = styled.h3`
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 15px;
  color: #ffffff;
`;

const FormGroup = styled.div`
  margin-bottom: 20px;
`;

const Label = styled.label`
  display: block;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 8px;
  color: #e0e0e0;
`;

const Input = styled.input`
  width: 100%;
  padding: 12px;
  border: 1px solid #404040;
  border-radius: 6px;
  background-color: #2d2d2d;
  color: #ffffff;
  font-size: 14px;
  
  &:focus {
    outline: none;
    border-color: #ff4444;
  }
  
  &::placeholder {
    color: #888;
  }
`;

const StyledDatePicker = styled(DatePicker)`
  width: 100%;
  padding: 12px;
  border: 1px solid #404040;
  border-radius: 6px;
  background-color: #2d2d2d;
  color: #ffffff;
  font-size: 14px;
  cursor: pointer;
  
  &:focus {
    outline: none;
    border-color: #ff4444;
  }
  
  &::placeholder {
    color: #888;
  }
`;

const SearchButton = styled.button`
  width: 100%;
  padding: 15px;
  background: linear-gradient(180deg, #ff5a5a 0%, #ff4444 100%);
  color: #ffffff;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: background-color 0.2s;
  margin-top: 20px;
  
  &:hover {
    background: linear-gradient(180deg, #ff6d6d 0%, #ff5656 100%);
  }
  
  &:disabled {
    background-color: #666;
    cursor: not-allowed;
  }
`;

const MainContent = styled.div`
  flex: 1;
  padding: 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-start;
  overflow-y: auto;
`;

const Title = styled.h1`
  font-size: 32px;
  font-weight: 700;
  margin-bottom: 20px;
  text-align: center;
  display: flex;
  align-items: center;
  gap: 12px;
`;

const TitleIcon = styled.div`
  width: 40px;
  height: 40px;
  background-color: #ff4444;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  font-weight: bold;
`;

const Description = styled.div`
  font-size: 18px;
  color: #cccccc;
  margin-bottom: 30px;
  text-align: center;
  max-width: 800px;
  line-height: 1.6;
`;

const DossierContainer = styled.div`
  width: 100%;
  max-width: 800px;
  margin-top: 20px;
  padding: 20px;
  background-color: #2a2a2a;
  border-radius: 8px;
  border: 1px solid #404040;
  color: #e0e0e0;
  white-space: pre-wrap;
`;

const ActionsBar = styled.div`
  position: sticky;
  bottom: 0;
  background: #2a2a2a;
  border-top: 1px solid #404040;
  padding: 12px 16px;
  display: flex;
  gap: 12px;
  justify-content: center;
  width: 100%;
`;

const Overlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: 999;
  display: ${props => props.isOpen ? 'block' : 'none'};
  
  @media (min-width: 769px) {
    display: none;
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

const Alert = styled.div`
  padding: 12px 16px;
  border-radius: 6px;
  margin-bottom: 15px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  
  &.error {
    background-color: #2a1a1a;
    border: 1px solid #ff4444;
    color: #ff6666;
  }
  
  &.warning {
    background-color: #2a2a1a;
    border: 1px solid #ffaa00;
    color: #ffcc00;
  }
`;

function App() {
  const [isMenuOpen, setIsMenuOpen] = useState(true);
  const [startDate, setStartDate] = useState(new Date(2023, 0, 1));
  const [endDate, setEndDate] = useState(new Date(2025, 7, 5));
  const [keyword, setKeyword] = useState('');
  const [senderEmail, setSenderEmail] = useState('');
  const [advancedQuery, setAdvancedQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedThreads, setSelectedThreads] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);
  const [keywordError, setKeywordError] = useState(false);
  const [isGeneratingDossier, setIsGeneratingDossier] = useState(false);
  const [dossier, setDossier] = useState(null);

  const handleSearch = async () => {
    setIsLoading(true);
    setError('');
    setWarning('');
    setSearchResults([]);
    setSelectedThreads([]);
    setAnalysisResults(null);
    setDossier(null);
    setKeywordError(false);

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
    } catch (error) {
      console.error('Error analyzing threads:', error);
      setError('An error occurred during analysis. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleGenerateDossier = async () => {
    if (!analysisResults) {
      setError('Analyze threads first to generate a dossier.');
      return;
    }
    setIsGeneratingDossier(true);
    setError('');
    try {
      const response = await axios.post('/api/generate_dossier', {
        analysis: {
          structured_analysis: analysisResults.structured_analysis,
          raw_analysis: analysisResults.analysis
        }
      });
      setDossier(response.data || null);
    } catch (e) {
      console.error('Error generating dossier:', e);
      setError('An error occurred while generating the dossier.');
    } finally {
      setIsGeneratingDossier(false);
    }
  };

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <AppContainer>
      <TopBar>
        <SectionTitle style={{ marginBottom: 12, display: 'flex', alignItems: 'center', gap: 8, fontSize: 18 }}>
          <Mail size={18} /> Search Emails
        </SectionTitle>
        <FiltersRow>
          <FormGroup>
            <Label>Start Date</Label>
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
            <Label>End Date</Label>
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
            <Label>Keyword <span style={{color: '#ff4444'}}>*</span></Label>
            <Input
              type="text"
              value={keyword}
              onChange={(e) => { setKeyword(e.target.value); setKeywordError(false); }}
              placeholder="Keyword (e.g., invoice, roadmap)"
              style={keywordError ? { borderColor: '#ff4444', background: '#2a1a1a' } : {}}
              required
            />
          </FormGroup>
          <FormGroup>
            <Label>Sender Email</Label>
            <Input
              type="email"
              value={senderEmail}
              onChange={(e) => setSenderEmail(e.target.value)}
              placeholder="from: someone@company.com"
            />
          </FormGroup>
          <FormGroup>
            <Label>Advanced Query</Label>
            <Input
              type="text"
              value={advancedQuery}
              onChange={(e) => setAdvancedQuery(e.target.value)}
              placeholder='subject:"invoice" has:attachment -in:chats'
            />
          </FormGroup>
        </FiltersRow>
        <div style={{ marginTop: 12 }}>
          <SearchButton onClick={handleSearch} disabled={isLoading}>
            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <Search size={20} />
            )}
            Find Relevant Emails
          </SearchButton>
        </div>
      </TopBar>
      
      <MainContent>
        <Title>
          <TitleIcon>📧</TitleIcon>
          Email Thread Analyzer
        </Title>
        
        <Description>
          Search and analyze your email threads to find relevant conversations and insights.
          <br />
          Use the menu on the left to set your search criteria and find relevant emails.
        </Description>
        
        {error && (
          <Alert className="error">
            {error}
          </Alert>
        )}
        
        {warning && (
          <Alert className="warning">
            {warning}
          </Alert>
        )}

        {searchResults.length > 0 && (
          <SearchResults
            results={searchResults}
            selectedThreads={selectedThreads}
            onThreadToggle={handleThreadToggle}
            onAnalyzeSelected={handleAnalyzeSelected}
            isLoading={isAnalyzing}
          />
        )}

        {analysisResults && (
          <AnalysisReport
            structuredAnalysis={analysisResults.structured_analysis}
            rawAnalysis={analysisResults.analysis}
          />
        )}

        {analysisResults && (
          <div style={{ width: '100%', display: 'flex', justifyContent: 'center', marginTop: 12 }}>
            <div style={{ maxWidth: 800, width: '100%' }}>
              <SearchButton onClick={handleGenerateDossier} disabled={isGeneratingDossier}>
                {isGeneratingDossier ? (
                  <LoadingSpinner />
                ) : (
                  <FileText size={18} />
                )}
                Generate Dossier
              </SearchButton>
            </div>
          </div>
        )}

        {dossier && (
          <DossierContainer>
            <h3 style={{ marginTop: 0, marginBottom: 12, color: '#fff' }}>Email Dossier</h3>
            <div>
              <h4 style={{ color: '#fff', marginBottom: 8 }}>Meeting Flow</h4>
              <div style={{ marginBottom: 16 }}>
                {dossier.meeting_flow || ''}
              </div>
              <h4 style={{ color: '#fff', marginBottom: 8 }}>Client Details</h4>
              <div>
                {dossier.client_details || 'Client Details: To be added.'}
              </div>
            </div>
          </DossierContainer>
        )}

        {selectedThreads.length > 0 && (
          <ActionsBar>
            <SearchButton onClick={handleAnalyzeSelected} disabled={isAnalyzing}>
              {isAnalyzing ? (
                <LoadingSpinner />
              ) : (
                <Mail size={18} />
              )}
              Analyze Selected ({selectedThreads.length})
            </SearchButton>
            <SearchButton onClick={() => setSelectedThreads([])} disabled={isAnalyzing}>
              Clear Selection
            </SearchButton>
          </ActionsBar>
        )}
      </MainContent>
    </AppContainer>
  );
}

export default App;