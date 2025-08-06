import React, { useState } from 'react';
import styled from 'styled-components';
import { Search, Menu, X, Mail } from 'lucide-react';
import axios from 'axios';
import { format } from 'date-fns';
import DatePicker from 'react-datepicker';
import "react-datepicker/dist/react-datepicker.css";
import SearchResults from './components/SearchResults';
import AnalysisReport from './components/AnalysisReport';

const AppContainer = styled.div`
  display: flex;
  min-height: 100vh;
  background-color: #1a1a1a;
  color: #ffffff;
`;

const Sidebar = styled.div`
  width: 350px;
  background-color: #2a2a2a;
  padding: 20px;
  border-right: 1px solid #404040;
  position: relative;
  transition: transform 0.3s ease;
  
  @media (max-width: 768px) {
    position: fixed;
    top: 0;
    left: 0;
    height: 100vh;
    z-index: 1000;
    transform: ${props => props.isOpen ? 'translateX(0)' : 'translateX(-100%)'};
  }
`;

const MenuToggle = styled.button`
  position: absolute;
  top: 20px;
  left: 20px;
  background: none;
  border: none;
  color: #ffffff;
  cursor: pointer;
  font-size: 18px;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 6px;
  transition: background-color 0.2s;
  
  &:hover {
    background-color: #404040;
  }
`;

const SidebarContent = styled.div`
  margin-top: 60px;
`;

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
  background-color: #333;
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
  background-color: #333;
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
  background-color: #ff4444;
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
    background-color: #ff6666;
  }
  
  &:disabled {
    background-color: #666;
    cursor: not-allowed;
  }
`;

const MainContent = styled.div`
  flex: 1;
  padding: 40px;
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

const MobileMenuButton = styled.button`
  position: fixed;
  top: 20px;
  left: 20px;
  background: #2a2a2a;
  border: none;
  color: #ffffff;
  cursor: pointer;
  padding: 10px;
  border-radius: 6px;
  z-index: 1001;
  display: none;
  
  @media (max-width: 768px) {
    display: flex;
    align-items: center;
    justify-content: center;
  }
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
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [warning, setWarning] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedThreads, setSelectedThreads] = useState([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResults, setAnalysisResults] = useState(null);

  const handleSearch = async () => {
    setIsLoading(true);
    setError('');
    setWarning('');
    setSearchResults([]);
    setSelectedThreads([]);
    setAnalysisResults(null);
    
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
        from_email: senderEmail || null
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

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  return (
    <AppContainer>
      <MobileMenuButton onClick={toggleMenu}>
        <Menu size={20} />
      </MobileMenuButton>
      
      <Overlay isOpen={isMenuOpen} onClick={toggleMenu} />
      
      <Sidebar isOpen={isMenuOpen}>
        <MenuToggle onClick={toggleMenu}>
          <X size={20} />
        </MenuToggle>
        
        <SidebarContent>
          <Section>
            <SectionTitle>Date Range</SectionTitle>
            
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
          </Section>
          
          <Section>
            <SectionTitle>Search Options</SectionTitle>
            
            <FormGroup>
              <Label>Keyword</Label>
              <Input
                type="text"
                value={keyword}
                onChange={(e) => setKeyword(e.target.value)}
                placeholder="Search email thread subjects by keyword"
              />
            </FormGroup>
            
            <FormGroup>
              <Label>Sender Email</Label>
              <Input
                type="email"
                value={senderEmail}
                onChange={(e) => setSenderEmail(e.target.value)}
                placeholder="Filter emails by sender email"
              />
            </FormGroup>
          </Section>
          
          <SearchButton onClick={handleSearch} disabled={isLoading}>
            {isLoading ? (
              <LoadingSpinner />
            ) : (
              <Search size={20} />
            )}
            Find Relevant Emails
          </SearchButton>
        </SidebarContent>
      </Sidebar>
      
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
          <AnalysisReport analysis={analysisResults.analysis} />
        )}
      </MainContent>
    </AppContainer>
  );
}

export default App;