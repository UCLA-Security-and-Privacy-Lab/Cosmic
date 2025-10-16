#!/usr/bin/env python3
"""
RAG-based Consent-related Content Identification System

This module implements a Retrieval Augmented Generation (RAG) system to extract 
consent-related content from privacy policies using diverse prompts to cover 
multiple consent dimensions.
"""

import os
import json
import argparse
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter


@dataclass
class ConsentQuery:
    """Represents a consent-related query with its purpose and prompt."""
    purpose: str
    query_text: str
    description: str


class ConsentRAGAnalyzer:
    """
    RAG-based analyzer for extracting consent-related content from privacy policies.
    
    This class implements the methodology described in the paper:
    - Constructs a knowledge base by embedding privacy policies
    - Indexes them into a vector database
    - Uses diverse prompts to cover multiple consent dimensions
    """
    
    def __init__(self, chroma_path: str = "chroma", policy_file: str = None):
        """
        Initialize the Consent RAG Analyzer.
        
        Args:
            chroma_path: Path to the Chroma vector database
            policy_file: Path to privacy policy file (if creating new database)
        """
            
        self.chroma_path = chroma_path
        self.embedding_function = OpenAIEmbeddings()
        
        # Initialize database
        if policy_file and not os.path.exists(chroma_path):
            print(f"Creating new vector database from {policy_file}...")
            self._create_database_from_file(policy_file)
        
        self.db = Chroma(persist_directory=chroma_path, embedding_function=self.embedding_function)
        
        # Define the diverse set of consent-related queries
        self.consent_queries = self._initialize_consent_queries()
    
    def _create_database_from_file(self, policy_file: str):
        """
        Create vector database from privacy policy file.
        
        Args:
            policy_file: Path to the privacy policy file
        """
        print(f"Loading privacy policy from: {policy_file}")
        
        # Load the document
        loader = TextLoader(policy_file, encoding='utf-8')
        documents = loader.load()
        
        print(f"Document loaded: {len(documents)} pages")
        
        # Split documents into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
        
        chunks = text_splitter.split_documents(documents)
        print(f"Document split into {len(chunks)} chunks")
        
        # Add metadata to each chunk
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'source': policy_file,
                'chunk_id': i,
                'chunk_size': len(chunk.page_content)
            })
        
        # Create and save vector database
        db = Chroma.from_documents(
            documents=chunks,
            embedding=self.embedding_function,
            persist_directory=self.chroma_path
        )
        
        print(f"✅ Vector database created and saved to {self.chroma_path}")
    
    
    def _filter_relevant_sentences(self, sentences: List[str], query: str) -> List[str]:
        """Filter sentences that are likely relevant to the query."""
        query_words = set(query.lower().split())
        relevant_sentences = []
        
        for sentence in sentences:
            sentence_words = set(sentence.lower().split())
            # Check for keyword overlap
            overlap = len(query_words.intersection(sentence_words))
            if overlap > 0 or any(word in sentence.lower() for word in ['consent', 'agree', 'permission', 'authorize']):
                relevant_sentences.append(sentence)
        
        return relevant_sentences
        
    def _initialize_consent_queries(self) -> List[ConsentQuery]:
        """
        Initialize the diverse set of prompts to cover multiple consent dimensions.
        """
        return [
            ConsentQuery(
                purpose="consent_actions",
                query_text="what user actions are required to give consent",
                description="Identifies specific user actions needed to provide consent"
            ),
            ConsentQuery(
                purpose="consent_withdrawal",
                query_text="how users can withdraw consent",
                description="Finds information about consent withdrawal procedures"
            ),
            ConsentQuery(
                purpose="consent_legal_basis",
                query_text="whether consent is cited as a legal basis",
                description="Determines if consent is used as a legal basis for data processing"
            ),
            ConsentQuery(
                purpose="consent_purposes",
                query_text="for what purposes consent is requested",
                description="Identifies the specific purposes for which consent is sought"
            )
        ]
    
 
    
    def analyze_consent_content(self, 
                              query: ConsentQuery, 
                              top_k: int = 15, 
                              relevance_threshold: float = 0.65,
                              return_full_chunks: bool = True) -> Dict[str, Any]:
        """
        Analyze consent-related content for a specific query.
        
        Args:
            query: The consent query to analyze
            top_k: Number of top documents to retrieve
            relevance_threshold: Minimum relevance score threshold
            
        Returns:
            Dictionary containing analysis results and metadata
        """
        try:
            # Retrieve relevant documents using similarity search
            results = self.db.similarity_search_with_relevance_scores(
                query.query_text, 
                k=top_k
            )
            
            if not results or results[0][1] < relevance_threshold:
                return {
                    'query_purpose': query.purpose,
                    'query_text': query.query_text,
                    'description': query.description,
                    'retrieved_sentences': [],
                    'relevance_score': results[0][1] if results else 0.0,
                    'sources': [],
                    'status': 'no_results'
                }
            
            # Extract content from retrieved documents
            retrieved_sentences = []
            sources = []
            relevance_scores = []
            
            for doc, score in results:
                if score >= relevance_threshold:
                    content = doc.page_content.strip()
                    
                    if return_full_chunks:
                        # Return full content chunks for better context
                        if len(content) >= 20:  # Minimum content length
                            retrieved_sentences.append({
                                'sentence': content,  # Full chunk content
                                'source': doc.metadata.get("source", "Unknown"),
                                'chunk_id': doc.metadata.get("chunk_id", 0),
                                'relevance_score': score,
                                'content_type': 'full_chunk'
                            })
                    else:
                        # Split into sentences for more granular results
                        sentences = content
                        relevant_sentences = self._filter_relevant_sentences(sentences, query.query_text)
                        
                        for sentence in relevant_sentences:
                            retrieved_sentences.append({
                                'sentence': sentence.strip(),
                                'source': doc.metadata.get("source", "Unknown"),
                                'chunk_id': doc.metadata.get("chunk_id", 0),
                                'relevance_score': score,
                                'content_type': 'sentence'
                            })
                    
                    sources.append(doc.metadata.get("source", "Unknown"))
                    relevance_scores.append(score)
            
            return {
                'query_purpose': query.purpose,
                'query_text': query.query_text,
                'description': query.description,
                'retrieved_sentences': retrieved_sentences,
                'relevance_scores': relevance_scores,
                'sources': list(set(sources)),
                'status': 'success',
                'num_sentences_retrieved': len(retrieved_sentences)
            }
            
        except Exception as e:
            return {
                'query_purpose': query.purpose,
                'query_text': query.query_text,
                'description': query.description,
                'retrieved_sentences': [],
                'sources': [],
                'status': 'error',
                'error': str(e)
            }
    
    def comprehensive_consent_analysis(self, 
                                     top_k: int = 5, 
                                     relevance_threshold: float = 0.65,
                                     return_full_chunks: bool = True) -> Dict[str, Any]:
        """
        Perform comprehensive consent analysis using all defined queries.
        
        This implements the paper's methodology of using "a diverse set of prompts 
        to cover more consent dimensions."
        
        Args:
            top_k: Number of top documents to retrieve per query
            relevance_threshold: Minimum relevance score threshold
            return_full_chunks: If True, return full content chunks; if False, split into sentences
            
        Returns:
            Dictionary containing comprehensive analysis results
        """
        print("Starting comprehensive consent analysis...")
        print(f"Using {len(self.consent_queries)} diverse consent queries")
        
        results = {
            'analysis_timestamp': None,
            'total_queries': len(self.consent_queries),
            'successful_queries': 0,
            'failed_queries': 0,
            'consent_dimensions': {},
            'summary': {}
        }
        
        import datetime
        results['analysis_timestamp'] = datetime.datetime.now().isoformat()
        
        # Analyze each consent dimension
        for i, query in enumerate(self.consent_queries, 1):
            print(f"Processing query {i}/{len(self.consent_queries)}: {query.purpose}")
            
            analysis_result = self.analyze_consent_content(
                query, top_k, relevance_threshold, return_full_chunks
            )
            
            results['consent_dimensions'][query.purpose] = analysis_result
            
            if analysis_result['status'] == 'success':
                results['successful_queries'] += 1
            else:
                results['failed_queries'] += 1
        
        # Generate summary
        results['summary'] = self._generate_analysis_summary(results['consent_dimensions'])
        
        print(f"Analysis completed: {results['successful_queries']} successful, {results['failed_queries']} failed")
        
        return results
    
    def _generate_analysis_summary(self, consent_dimensions: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the consent analysis results."""
        summary = {
            'total_dimensions_analyzed': len(consent_dimensions),
            'dimensions_with_content': 0,
            'key_findings': [],
            'consent_actions_found': False,
            'withdrawal_procedures_found': False,
            'legal_basis_citations': False,
            'purpose_specificity': 'unknown'
        }
        
        for purpose, result in consent_dimensions.items():
            if result['status'] == 'success' and len(result.get('retrieved_sentences', [])) > 0:
                summary['dimensions_with_content'] += 1
                
                if purpose == 'consent_actions':
                    summary['consent_actions_found'] = True
                elif purpose == 'consent_withdrawal':
                    summary['withdrawal_procedures_found'] = True
                elif purpose == 'consent_legal_basis':
                    summary['legal_basis_citations'] = True
                
                summary['key_findings'].append({
                    'dimension': purpose,
                    'description': result['description'],
                    'sources_count': len(result['sources']),
                    'sentences_count': len(result.get('retrieved_sentences', []))
                })
        
        return summary
    
    def save_results(self, results: Dict[str, Any], output_path: str = "consent_analysis_results.json"):
        """Save analysis results to a JSON file."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Results saved to {output_path}")


def main():
    """Main function for command-line usage."""
    parser = argparse.ArgumentParser(
        description="RAG-based Consent Content Analysis for Privacy Policies"
    )
    parser.add_argument(
        "--chroma-path", 
        default="chroma", 
        help="Path to Chroma vector database"
    )
    parser.add_argument(
        "--policy-file",
        help="Path to privacy policy file (will create database if not exists)"
    )
    parser.add_argument(
        "--output", 
        default="consent_analysis_results.json", 
        help="Output file path for results"
    )
    parser.add_argument(
        "--top-k", 
        type=int, 
        default=5, 
        help="Number of top documents to retrieve per query"
    )
    parser.add_argument(
        "--threshold", 
        type=float, 
        default=0.65, 
        help="Relevance score threshold"
    )
    parser.add_argument(
        "--api-key", 
        help="OpenAI API key (if not set in environment)"
    )
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = ConsentRAGAnalyzer(
        chroma_path=args.chroma_path,
        policy_file=args.policy_file
    )
    
    # Perform comprehensive analysis
    results = analyzer.comprehensive_consent_analysis(
        top_k=args.top_k,
        relevance_threshold=args.threshold
    )
    
    # Save results
    analyzer.save_results(results, args.output)
    
    


if __name__ == "__main__":
    main()
