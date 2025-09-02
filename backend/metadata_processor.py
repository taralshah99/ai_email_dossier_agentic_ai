"""
Multi-Thread Metadata Processor

This module provides efficient and clear metadata processing for multiple email threads.
It handles participant extraction, date processing, thread metadata, and combined metadata
in a structured and maintainable way.
"""

import re
from datetime import datetime
from typing import Dict, List, Set, Optional, Tuple
from email.utils import parsedate_to_datetime
import base64


class ThreadRelevancyAnalyzer:
    """Analyzes relevancy between email threads based on participants and content."""
    
    def __init__(self):
        self.participant_weight = 0.6  # Weight for participant overlap
        self.content_weight = 0.4     # Weight for content similarity
    
    def analyze_thread_relevancy(self, thread_metadatas: List['ThreadMetadata']) -> Dict[str, any]:
        """
        Analyze relevancy between threads and group them accordingly.
        
        Returns:
            Dictionary containing:
            - relevant_groups: List of groups with relevant threads
            - irrelevant_threads: List of threads that don't fit any group
            - relevancy_matrix: Matrix showing relevancy scores between threads
        """
        if len(thread_metadatas) < 2:
            return {
                "relevant_groups": [thread_metadatas] if thread_metadatas else [],
                "irrelevant_threads": [],
                "relevancy_matrix": {}
            }
        
        # Calculate relevancy matrix between all thread pairs
        relevancy_matrix = self._calculate_relevancy_matrix(thread_metadatas)
        
        # Group threads based on relevancy
        relevant_groups, irrelevant_threads = self._group_threads_by_relevancy(
            thread_metadatas, relevancy_matrix
        )
        
        return {
            "relevant_groups": relevant_groups,
            "irrelevant_threads": irrelevant_threads,
            "relevancy_matrix": relevancy_matrix
        }
    
    def _calculate_relevancy_matrix(self, thread_metadatas: List['ThreadMetadata']) -> Dict[str, float]:
        """Calculate relevancy scores between all thread pairs."""
        matrix = {}
        
        for i, thread1 in enumerate(thread_metadatas):
            for j, thread2 in enumerate(thread_metadatas):
                if i >= j:  # Skip diagonal and lower triangle
                    continue
                
                pair_key = f"{thread1.thread_id}_{thread2.thread_id}"
                
                # Calculate participant overlap score
                participant_score = self._calculate_participant_overlap(
                    thread1.participants, thread2.participants
                )
                
                # Calculate content similarity score
                content_score = self._calculate_content_similarity(
                    thread1.content_snippets, thread2.content_snippets
                )
                
                # Calculate subject similarity score
                subject_score = self._calculate_subject_similarity(
                    thread1.subject, thread2.subject
                )
                
                # Combined relevancy score
                relevancy_score = (
                    self.participant_weight * participant_score +
                    (1 - self.participant_weight) * (0.7 * content_score + 0.3 * subject_score)
                )
                
                matrix[pair_key] = relevancy_score
                
                # Only print if score is above threshold or very close
                if relevancy_score >= 0.4:  # Show scores close to threshold
                    print(f"[ThreadRelevancyAnalyzer] Relevancy {thread1.subject[:30]} vs {thread2.subject[:30]}: "
                          f"participant={participant_score:.2f}, content={content_score:.2f}, "
                          f"subject={subject_score:.2f}, total={relevancy_score:.2f}")
        
        return matrix
    
    def _calculate_participant_overlap(self, participants1: Dict, participants2: Dict) -> float:
        """Calculate participant overlap between two threads."""
        if not participants1 or not participants2:
            return 0.0
        
        # Extract all participant emails from both threads
        emails1 = set()
        emails2 = set()
        
        for participant in participants1.values():
            if isinstance(participant, dict) and "email" in participant:
                emails1.add(participant["email"].lower())
        
        for participant in participants2.values():
            if isinstance(participant, dict) and "email" in participant:
                emails2.add(participant["email"].lower())
        
        if not emails1 or not emails2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(emails1.intersection(emails2))
        union = len(emails1.union(emails2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_content_similarity(self, content1: List[str], content2: List[str]) -> float:
        """Calculate content similarity between two threads."""
        if not content1 or not content2:
            return 0.0
        
        # Combine content snippets
        text1 = " ".join(content1).lower()
        text2 = " ".join(content2).lower()
        
        # Extract meaningful words (remove common words)
        words1 = set(re.findall(r'\b[a-z]{3,}\b', text1))
        words2 = set(re.findall(r'\b[a-z]{3,}\b', text2))
        
        # Remove common English words
        common_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'within', 'without',
            'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
            'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'mine', 'yours', 'his', 'hers', 'ours', 'theirs',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
            'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might',
            'can', 'must', 'shall', 'am', 'pm', 'yes', 'no', 'not', 'very', 'just',
            'now', 'then', 'here', 'there', 'when', 'where', 'why', 'how', 'all',
            'any', 'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such',
            'only', 'own', 'same', 'so', 'than', 'too', 'also', 'around', 'away',
            'back', 'down', 'even', 'ever', 'far', 'forward', 'further', 'here',
            'however', 'indeed', 'instead', 'later', 'least', 'maybe', 'meanwhile',
            'moreover', 'much', 'near', 'never', 'next', 'often', 'once', 'perhaps',
            'quite', 'rather', 'really', 'since', 'soon', 'still', 'though', 'thus',
            'together', 'under', 'until', 'well', 'whether', 'while', 'yet'
        }
        
        words1 = words1 - common_words
        words2 = words2 - common_words
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_subject_similarity(self, subject1: str, subject2: str) -> float:
        """Calculate subject similarity between two threads."""
        if not subject1 or not subject2:
            return 0.0
        
        # Normalize subjects
        subj1 = subject1.lower().strip()
        subj2 = subject2.lower().strip()
        
        # Remove common prefixes
        prefixes_to_remove = ['re:', 'fw:', 'fwd:', 'fw:', 'fwd:']
        for prefix in prefixes_to_remove:
            if subj1.startswith(prefix):
                subj1 = subj1[len(prefix):].strip()
            if subj2.startswith(prefix):
                subj2 = subj2[len(prefix):].strip()
        
        # Extract words
        words1 = set(re.findall(r'\b[a-z]{2,}\b', subj1))
        words2 = set(re.findall(r'\b[a-z]{2,}\b', subj2))
        
        if not words1 or not words2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _group_threads_by_relevancy(self, thread_metadatas: List['ThreadMetadata'], 
                                   relevancy_matrix: Dict[str, float]) -> Tuple[List[List['ThreadMetadata']], List['ThreadMetadata']]:
        """Group threads based on relevancy scores."""
        if len(thread_metadatas) < 2:
            return [thread_metadatas] if thread_metadatas else [], []
        
        # Threshold for considering threads relevant
        relevancy_threshold = 0.5  # Increased from 0.3 to be more strict
        
        # Create graph of relevant connections
        relevant_connections = {}
        for pair_key, score in relevancy_matrix.items():
            if score >= relevancy_threshold:
                thread1_id, thread2_id = pair_key.split('_', 1)
                if thread1_id not in relevant_connections:
                    relevant_connections[thread1_id] = set()
                if thread2_id not in relevant_connections:
                    relevant_connections[thread2_id] = set()
                relevant_connections[thread1_id].add(thread2_id)
                relevant_connections[thread2_id].add(thread1_id)
        
        # Find connected components (groups) using a more robust approach
        visited = set()
        groups = []
        
        # First pass: find all connected components
        for thread in thread_metadatas:
            if thread.thread_id in visited:
                continue
            
            # Start new group
            group = []
            self._dfs_group(thread.thread_id, relevant_connections, visited, group, thread_metadatas)
            
            # Only add groups that have multiple threads OR single threads with no relevant connections
            if len(group) > 1:
                groups.append(group)
            elif len(group) == 1:
                # Check if this single thread has any relevant connections
                thread_id = group[0].thread_id
                has_connections = thread_id in relevant_connections and len(relevant_connections[thread_id]) > 0
                
                if not has_connections:
                    # This thread has no relevant connections, it's truly irrelevant
                    # Don't add it to groups - it will be caught in the irrelevant_threads section
                    pass
                else:
                    # This thread has connections but they might not be processed yet
                    # We'll handle this in a second pass
                    pass
        
        # Second pass: handle remaining connected threads
        # Find all threads that have connections but weren't grouped
        remaining_connected = set()
        for thread in thread_metadatas:
            thread_id = thread.thread_id
            if thread_id in relevant_connections and len(relevant_connections[thread_id]) > 0:
                # Check if this thread is already in a group
                in_group = False
                for group in groups:
                    if any(t.thread_id == thread_id for t in group):
                        in_group = True
                        break
                
                if not in_group:
                    remaining_connected.add(thread_id)
        
        print(f"[ThreadRelevancyAnalyzer] Second pass - remaining connected threads: {len(remaining_connected)}")
        for thread_id in remaining_connected:
            thread_obj = next((t for t in thread_metadatas if t.thread_id == thread_id), None)
            if thread_obj:
                print(f"    Remaining: {thread_obj.subject[:30]}")
        
        # Try to merge remaining connected threads into existing groups
        for thread_id in remaining_connected:
            thread_obj = next((t for t in thread_metadatas if t.thread_id == thread_id), None)
            if not thread_obj:
                continue
            
            # Find the best group to add this thread to
            best_group = None
            best_score = 0.0
            
            for group in groups:
                for group_thread in group:
                    pair_key = f"{thread_id}_{group_thread.thread_id}"
                    reverse_key = f"{group_thread.thread_id}_{thread_id}"
                    score = relevancy_matrix.get(pair_key, relevancy_matrix.get(reverse_key, 0.0))
                    if score > best_score:
                        best_score = score
                        best_group = group
            
            # Add to best group if score is above threshold
            if best_group and best_score >= relevancy_threshold:
                best_group.append(thread_obj)
                print(f"[ThreadRelevancyAnalyzer] Added {thread_obj.subject[:30]} to group with score {best_score:.3f}")
            else:
                # This thread couldn't be grouped, it's irrelevant
                print(f"[ThreadRelevancyAnalyzer] Could not group {thread_obj.subject[:30]} (best score: {best_score:.3f})")
        
        # Find irrelevant threads (not in any group)
        grouped_thread_ids = set()
        for group in groups:
            for thread in group:
                grouped_thread_ids.add(thread.thread_id)
        
        irrelevant_threads = [
            thread for thread in thread_metadatas 
            if thread.thread_id not in grouped_thread_ids
        ]
        
        print(f"[ThreadRelevancyAnalyzer] Grouping results:")
        print(f"  - Relevancy threshold: {relevancy_threshold}")
        print(f"  - Relevant groups: {len(groups)}")
        for i, group in enumerate(groups):
            print(f"    Group {i+1}: {[t.subject[:30] for t in group]}")
        print(f"  - Irrelevant threads: {len(irrelevant_threads)}")
        for thread in irrelevant_threads:
            print(f"    Irrelevant: {thread.subject[:30]}")
        
        # Debug: Show relevancy matrix for better understanding
        print(f"[ThreadRelevancyAnalyzer] Relevancy matrix:")
        for pair_key, score in relevancy_matrix.items():
            if score >= relevancy_threshold:
                thread1_id, thread2_id = pair_key.split('_', 1)
                thread1 = next((t for t in thread_metadatas if t.thread_id == thread1_id), None)
                thread2 = next((t for t in thread_metadatas if t.thread_id == thread2_id), None)
                if thread1 and thread2:
                    print(f"    {thread1.subject[:30]} <-> {thread2.subject[:30]}: {score:.3f}")
        
        return groups, irrelevant_threads
    
    def _dfs_group(self, thread_id: str, connections: Dict[str, set], visited: set, 
                   group: List['ThreadMetadata'], all_threads: List['ThreadMetadata']):
        """Depth-first search to find connected threads."""
        if thread_id in visited:
            return
        
        visited.add(thread_id)
        
        # Find the thread object
        thread_obj = None
        for thread in all_threads:
            if thread.thread_id == thread_id:
                thread_obj = thread
                break
        
        if thread_obj:
            group.append(thread_obj)
        
        # Visit connected threads
        if thread_id in connections:
            for connected_id in connections[thread_id]:
                self._dfs_group(connected_id, connections, visited, group, all_threads)


class ThreadMetadata:
    """Represents metadata for a single email thread."""
    
    def __init__(self, thread_id: str, subject: str, sender: str):
        self.thread_id = thread_id
        self.subject = subject
        self.sender = sender
        self.message_count = 0
        self.participants = {}
        self.dates = []
        self.first_email_date = None
        self.last_email_date = None
        self.content_snippets = []
        
    def add_message(self, message: dict):
        """Add a message to this thread's metadata."""
        self.message_count += 1
        
        # Extract content snippet
        if "snippet" in message:
            self.content_snippets.append(message["snippet"])
        elif message.get("payload", {}).get("parts"):
            for part in message["payload"]["parts"]:
                if part.get("mimeType") == "text/plain" and part.get("body", {}).get("data"):
                    try:
                        content = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                        self.content_snippets.append(content)
                    except Exception:
                        pass
        
        # Extract date
        headers = message.get("payload", {}).get("headers", [])
        for header in headers:
            if header.get("name", "").lower() == "date":
                try:
                    date_value = header.get("value", "")
                    if date_value:
                        date_obj = parsedate_to_datetime(date_value)
                        if date_obj:
                            self.dates.append(date_obj)
                except Exception:
                    pass
    
    def finalize(self):
        """Finalize the thread metadata after all messages are processed."""
        if self.dates:
            self.dates.sort()
            self.first_email_date = self.dates[0].strftime("%Y-%m-%d %H:%M:%S")
            self.last_email_date = self.dates[-1].strftime("%Y-%m-%d %H:%M:%S")
    
    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "thread_id": self.thread_id,
            "subject": self.subject,
            "sender": self.sender,
            "message_count": self.message_count,
            "participants": self.participants,
            "first_email_date": self.first_email_date,
            "last_email_date": self.last_email_date,
            "content_snippets": self.content_snippets
        }


class ParticipantManager:
    """Manages participant extraction and consolidation across multiple threads."""
    
    def __init__(self, gmail_service=None):
        self.gmail_service = gmail_service
        self.gmail_user_email = self._get_gmail_user_email()
        self.combined_participants = {}
        self.header_stats = {"from": 0, "to": 0, "cc": 0, "bcc": 0}
    
    def _get_gmail_user_email(self) -> Optional[str]:
        """Get Gmail user's email address."""
        if not self.gmail_service:
            return None
        
        try:
            from gmail_utils import get_gmail_user_profile
            profile = get_gmail_user_profile(self.gmail_service)
            if profile:
                return profile.get("emailAddress", "").lower()
        except Exception as e:
            print(f"[ParticipantManager] Error getting Gmail user profile: {e}")
        return None
    
    def extract_participants_from_messages(self, messages: List[dict]) -> Dict[str, dict]:
        """Extract participants from a list of email messages."""
        participants = {}
        
        for message in messages:
            headers = message.get("payload", {}).get("headers", [])
            
            for header in headers:
                name = header.get("name", "").lower()
                value = header.get("value", "")
                
                if name in ["from", "to", "cc", "bcc"]:
                    self.header_stats[name] += 1
                    self._process_email_addresses(value, name, participants)
        
        # Add Gmail user if not already present
        if self.gmail_user_email and self.gmail_user_email not in participants:
            self._add_gmail_user(participants)
        
        return participants
    
    def _process_email_addresses(self, value: str, header_type: str, participants: Dict[str, dict]):
        """Process email addresses from a header value."""
        if not value:
            return
        
        addresses = [addr.strip() for addr in value.split(",")]
        
        for addr in addresses:
            if "@" in addr:
                email_match = re.search(r'<([^>]+)>|([^\s<>]+@[^\s<>]+)', addr)
                if email_match:
                    email_addr = email_match.group(1) or email_match.group(2)
                    email_addr = email_addr.strip().lower()
                    
                    # Extract display name
                    display_name = re.sub(r'<[^>]+>', '', addr).strip().strip('"\'')
                    
                    # Generate display name if not found
                    if not display_name or display_name == email_addr:
                        display_name = self._generate_display_name(email_addr)
                    
                    # Add or update participant
                    if email_addr not in participants:
                        participants[email_addr] = {
                            "email": email_addr,
                            "display_name": display_name,
                            "roles": set([header_type])
                        }
                    else:
                        participants[email_addr]["roles"].add(header_type)
    
    def _generate_display_name(self, email: str) -> str:
        """Generate a display name from email address."""
        local_part = email.split('@')[0]
        
        if '.' in local_part:
            name_parts = [part for part in local_part.split('.') if part]
            return ' '.join(part.capitalize() for part in name_parts)
        elif '_' in local_part:
            name_parts = [part for part in local_part.split('_') if part]
            return ' '.join(part.capitalize() for part in name_parts)
        else:
            return local_part.capitalize()
    
    def _add_gmail_user(self, participants: Dict[str, dict]):
        """Add Gmail user to participants."""
        display_name = self._generate_display_name(self.gmail_user_email)
        
        participants[self.gmail_user_email] = {
            "email": self.gmail_user_email,
            "display_name": display_name,
            "roles": set(["gmail_user"])
        }
    
    def merge_participants(self, thread_participants: Dict[str, dict]):
        """Merge thread participants into combined participants."""
        for email, participant in thread_participants.items():
            if email not in self.combined_participants:
                self.combined_participants[email] = participant
            else:
                # Merge roles
                existing_roles = set(self.combined_participants[email]["roles"])
                new_roles = set(participant["roles"])
                self.combined_participants[email]["roles"] = list(existing_roles.union(new_roles))
    
    def get_combined_participants(self) -> Dict[str, dict]:
        """Get combined participants with roles as lists for JSON serialization."""
        result = {}
        for email, participant in self.combined_participants.items():
            result[email] = {
                "email": participant["email"],
                "display_name": participant["display_name"],
                "roles": list(participant["roles"])
            }
        return result


class MultiThreadMetadataProcessor:
    """Main processor for handling metadata across multiple email threads."""
    
    def __init__(self, gmail_service):
        self.gmail_service = gmail_service
        self.participant_manager = ParticipantManager(gmail_service)
        self.relevancy_analyzer = ThreadRelevancyAnalyzer()
        self.thread_metadatas = []
        self.all_dates = []
        self.all_subjects = []
        self.all_content = []
        self.relevancy_analysis = None
    
    def process_threads(self, thread_ids: List[str]) -> Dict[str, any]:
        """
        Process metadata for multiple threads.
        
        Returns:
            Dictionary containing:
            - combined_metadata: Consolidated metadata across all threads
            - thread_metadatas: Individual thread metadata
            - all_subjects: List of all thread subjects
            - all_content: Combined content for AI analysis
        """
        print(f"[MultiThreadMetadataProcessor] Processing {len(thread_ids)} threads...")
        
        for thread_id in thread_ids:
            try:
                self._process_single_thread(thread_id)
            except Exception as e:
                print(f"[MultiThreadMetadataProcessor] Critical error processing thread {thread_id}: {e}")
                import traceback
                traceback.print_exc()
                # Continue with other threads instead of stopping
                continue
        
        # Finalize all thread metadata
        for thread_meta in self.thread_metadatas:
            thread_meta.finalize()
        
        # Sort all dates
        self.all_dates.sort()
        
        # Analyze thread relevancy and grouping
        self.relevancy_analysis = self.relevancy_analyzer.analyze_thread_relevancy(self.thread_metadatas)
        
        # Convert ThreadMetadata objects to dictionaries in relevancy_analysis
        serializable_relevancy_analysis = {
            "relevant_groups": [
                [thread.to_dict() for thread in group] 
                for group in self.relevancy_analysis["relevant_groups"]
            ],
            "irrelevant_threads": [
                thread.to_dict() for thread in self.relevancy_analysis["irrelevant_threads"]
            ],
            "relevancy_matrix": self.relevancy_analysis["relevancy_matrix"]
        }
        
        # Create combined metadata
        combined_metadata = self._create_combined_metadata()
        
        print(f"[MultiThreadMetadataProcessor] Processing complete:")
        print(f"  - Threads processed: {len(self.thread_metadatas)}")
        print(f"  - Total participants: {len(self.participant_manager.combined_participants)}")
        print(f"  - Date range: {self.all_dates[0] if self.all_dates else 'None'} to {self.all_dates[-1] if self.all_dates else 'None'}")
        print(f"  - Relevant groups: {len(self.relevancy_analysis['relevant_groups'])}")
        print(f"  - Irrelevant threads: {len(self.relevancy_analysis['irrelevant_threads'])}")
        
        return {
            "combined_metadata": combined_metadata,
            "thread_metadatas": [t.to_dict() for t in self.thread_metadatas],
            "all_subjects": self.all_subjects,
            "all_content": self.all_content,
            "participant_stats": self.participant_manager.header_stats,
            "relevancy_analysis": serializable_relevancy_analysis
        }
    
    def _process_single_thread(self, thread_id: str):
        """Process metadata for a single thread."""
        try:
            # Get thread basic info
            subject, sender = self._get_thread_subject_and_sender(thread_id)
            
            # Handle cases where subject might be None, empty, or 'No Subject'
            if not subject or subject == 'No Subject' or subject.strip() == '':
                print(f"[MultiThreadMetadataProcessor] Thread {thread_id} has no subject, using thread ID as subject")
                subject = f"Thread {thread_id[:8]}..."  # Use truncated thread ID as subject
            
            # Handle cases where sender might be None or empty
            if not sender or sender == 'Unknown Sender' or sender.strip() == '':
                print(f"[MultiThreadMetadataProcessor] Thread {thread_id} has no sender, using 'Unknown'")
                sender = 'Unknown'
            
            # Create thread metadata object
            thread_meta = ThreadMetadata(thread_id, subject, sender)
            
            # Get messages
            messages = self._get_email_thread(thread_id)
            if not messages:
                print(f"[MultiThreadMetadataProcessor] Thread {thread_id} has no messages, creating empty thread metadata")
                # Create thread metadata even if no messages
                thread_meta = ThreadMetadata(thread_id, subject, sender)
                self.thread_metadatas.append(thread_meta)
                self.all_subjects.append(subject)
                print(f"[MultiThreadMetadataProcessor] Added empty thread: {subject}")
                return
            
            # Process each message
            for message in messages:
                thread_meta.add_message(message)
            
            # Extract participants
            thread_participants = self.participant_manager.extract_participants_from_messages(messages)
            thread_meta.participants = thread_participants
            
            # Merge participants
            self.participant_manager.merge_participants(thread_participants)
            
            # Add to collections
            self.thread_metadatas.append(thread_meta)
            self.all_subjects.append(subject)
            self.all_dates.extend(thread_meta.dates)
            
            # Prepare content for AI analysis
            content = self._prepare_thread_content(thread_meta, messages)
            self.all_content.append(content)
            
            print(f"[MultiThreadMetadataProcessor] Processed thread: {subject} ({len(messages)} messages, {len(thread_participants)} participants)")
            
        except Exception as e:
            print(f"[MultiThreadMetadataProcessor] Error processing thread {thread_id}: {e}")
    
    def _get_thread_subject_and_sender(self, thread_id: str) -> Tuple[str, str]:
        """Get thread subject and sender."""
        try:
            from app import get_thread_subject_and_sender
            return get_thread_subject_and_sender(self.gmail_service, thread_id)
        except Exception as e:
            print(f"[MultiThreadMetadataProcessor] Error getting thread subject/sender for {thread_id}: {e}")
            return "No Subject", "Unknown Sender"
    
    def _get_email_thread(self, thread_id: str) -> List[dict]:
        """Get email thread messages."""
        try:
            from app import get_email_thread
            return get_email_thread(self.gmail_service, thread_id)
        except Exception as e:
            print(f"[MultiThreadMetadataProcessor] Error getting email thread for {thread_id}: {e}")
            return []
    
    def _prepare_thread_content(self, thread_meta: ThreadMetadata, messages: List[dict]) -> str:
        """Prepare thread content for AI analysis."""
        # Extract email metadata for client name inference
        metadata_str = self._format_email_metadata(messages)
        
        # Combine content snippets
        content = "\n".join(thread_meta.content_snippets)
        
        # Combine metadata and content
        return f"=== THREAD: {thread_meta.subject} ===\n{metadata_str}\n\n{content}"
    
    def _format_email_metadata(self, messages: List[dict]) -> str:
        """Format email metadata for AI analysis."""
        try:
            from app import format_email_metadata
            return format_email_metadata(messages)
        except Exception as e:
            print(f"[MultiThreadMetadataProcessor] Error formatting email metadata: {e}")
            return "Email Participants' Companies (from metadata): Unknown"
    
    def _create_combined_metadata(self) -> Dict[str, any]:
        """Create combined metadata across all threads."""
        # Safely handle date calculations
        first_date = None
        last_date = None
        date_range_days = 0
        
        if self.all_dates and len(self.all_dates) > 0:
            first_date = self.all_dates[0].strftime("%Y-%m-%d %H:%M:%S")
            last_date = self.all_dates[-1].strftime("%Y-%m-%d %H:%M:%S")
            if len(self.all_dates) > 1:
                date_range_days = (self.all_dates[-1] - self.all_dates[0]).days
        
        return {
            "thread_count": len(self.thread_metadatas),
            "total_participants": len(self.participant_manager.combined_participants),
            "participants": self.participant_manager.get_combined_participants(),
            "first_email_date": first_date,
            "last_email_date": last_date,
            "threads": [t.to_dict() for t in self.thread_metadatas],
            "total_messages": sum(t.message_count for t in self.thread_metadatas),
            "date_range_days": date_range_days
        }


def process_multiple_threads_metadata(thread_ids: List[str], gmail_service) -> Dict[str, any]:
    """
    Convenience function to process metadata for multiple threads.
    
    Args:
        thread_ids: List of thread IDs to process
        gmail_service: Authenticated Gmail service
        
    Returns:
        Dictionary with processed metadata
    """
    processor = MultiThreadMetadataProcessor(gmail_service)
    return processor.process_threads(thread_ids)
