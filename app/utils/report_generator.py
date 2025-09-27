"""
Advanced Report Generator with Visual Analytics
Creates comprehensive reports with charts, graphs, and professional formatting
"""

import os
import io
import base64
from datetime import datetime
from typing import Dict, List, Any, Optional
import logging
import json

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import seaborn as sns
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import streamlit as st

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedReportGenerator:
    """Generate advanced reports with visualizations and analytics"""
    
    def __init__(self):
        self.colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        self.report_style = getSampleStyleSheet()
        
    def analyze_text_statistics(self, results: Dict[str, str]) -> Dict[str, Any]:
        """Generate text statistics from analysis results"""
        stats = {}
        
        for section, content in results.items():
            if content and isinstance(content, str):
                words = content.split()
                sentences = content.split('.')
                
                stats[section] = {
                    'word_count': len(words),
                    'sentence_count': len([s for s in sentences if s.strip()]),
                    'character_count': len(content),
                    'avg_word_length': np.mean([len(word) for word in words]) if words else 0,
                    'avg_sentence_length': np.mean([len(s.split()) for s in sentences if s.strip()]) if sentences else 0
                }
        
        return stats
    
    def create_keyword_frequency_chart(self, results: Dict[str, str]) -> go.Figure:
        """Create a keyword frequency bar chart"""
        # Extract keywords from all sections
        all_text = ' '.join([text for text in results.values() if text])
        words = all_text.lower().split()
        
        # Filter out common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
        }
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum()).lower()
            if len(clean_word) > 3 and clean_word not in stop_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        # Get top 20 words
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if top_words:
            words, frequencies = zip(*top_words)
            
            fig = go.Figure(data=[
                go.Bar(
                    x=frequencies,
                    y=words,
                    orientation='h',
                    marker_color='#1f77b4',
                    text=frequencies,
                    textposition='outside'
                )
            ])
            
            fig.update_layout(
                title="Top Keywords Frequency",
                xaxis_title="Frequency",
                yaxis_title="Keywords",
                height=600,
                margin=dict(l=100, r=50, t=80, b=50)
            )
            
            return fig
        else:
            # Return empty figure if no keywords found
            fig = go.Figure()
            fig.add_annotation(text="No keywords found", showarrow=False, x=0.5, y=0.5)
            return fig
    
    def create_section_analysis_chart(self, stats: Dict[str, Dict]) -> go.Figure:
        """Create a comparison chart of different analysis sections"""
        sections = list(stats.keys())
        word_counts = [stats[section]['word_count'] for section in sections]
        sentence_counts = [stats[section]['sentence_count'] for section in sections]
        
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('Word Count by Section', 'Sentence Count by Section'),
            vertical_spacing=0.12
        )
        
        # Word count chart
        fig.add_trace(
            go.Bar(x=sections, y=word_counts, name='Word Count', marker_color='#1f77b4'),
            row=1, col=1
        )
        
        # Sentence count chart
        fig.add_trace(
            go.Bar(x=sections, y=sentence_counts, name='Sentence Count', marker_color='#ff7f0e'),
            row=2, col=1
        )
        
        fig.update_layout(
            height=700,
            title_text="Analysis Sections Statistics",
            showlegend=False
        )
        
        return fig
    
    def create_wordcloud(self, results: Dict[str, str]) -> str:
        """Generate word cloud and return as base64 string"""
        try:
            all_text = ' '.join([text for text in results.values() if text])
            
            if not all_text.strip():
                return None
                
            # Create word cloud
            wordcloud = WordCloud(
                width=800,
                height=400,
                background_color='white',
                max_words=100,
                colormap='viridis',
                relative_scaling=0.5
            ).generate(all_text)
            
            # Convert to base64
            img_buffer = io.BytesIO()
            plt.figure(figsize=(10, 5))
            plt.imshow(wordcloud, interpolation='bilinear')
            plt.axis('off')
            plt.tight_layout(pad=0)
            plt.savefig(img_buffer, format='png', bbox_inches='tight', dpi=150)
            plt.close()
            
            img_buffer.seek(0)
            img_str = base64.b64encode(img_buffer.read()).decode()
            return img_str
            
        except Exception as e:
            logger.error(f"Error creating word cloud: {str(e)}")
            return None
    
    def create_analysis_overview_chart(self, results: Dict[str, str]) -> go.Figure:
        """Create an overview pie chart of analysis components"""
        sections_with_content = []
        sections_empty = []
        
        section_names = {
            'summary': 'Summary',
            'methodology': 'Methodology',
            'citations': 'Citations',
            'gaps': 'Research Gaps',
            'keywords': 'Keywords',
            'detailed': 'Detailed Analysis'
        }
        
        for key, content in results.items():
            display_name = section_names.get(key, key.title())
            if content and content.strip():
                sections_with_content.append(display_name)
            else:
                sections_empty.append(display_name)
        
        labels = ['Completed Sections', 'Skipped Sections']
        values = [len(sections_with_content), len(sections_empty)]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.3,
                marker_colors=['#2ca02c', '#d62728']
            )
        ])
        
        fig.update_layout(
            title="Analysis Completeness Overview",
            annotations=[dict(text=f"{len(sections_with_content)}/{len(results)}<br>Completed", 
                            x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        
        return fig
    
    def generate_interactive_report(self, results: Dict[str, str], paper_name: str) -> Dict[str, Any]:
        """Generate an interactive report with all visualizations"""
        logger.info("Generating advanced interactive report...")
        
        # Generate statistics
        stats = self.analyze_text_statistics(results)
        
        # Create visualizations
        report_data = {
            'paper_name': paper_name,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'statistics': stats,
            'charts': {}
        }
        
        try:
            # Keyword frequency chart
            keyword_chart = self.create_keyword_frequency_chart(results)
            report_data['charts']['keyword_frequency'] = keyword_chart
            
            # Section analysis chart
            if stats:
                section_chart = self.create_section_analysis_chart(stats)
                report_data['charts']['section_analysis'] = section_chart
            
            # Analysis overview chart
            overview_chart = self.create_analysis_overview_chart(results)
            report_data['charts']['analysis_overview'] = overview_chart
            
            # Word cloud
            wordcloud_b64 = self.create_wordcloud(results)
            if wordcloud_b64:
                report_data['wordcloud'] = wordcloud_b64
            
            logger.info("Interactive report generated successfully!")
            return report_data
            
        except Exception as e:
            logger.error(f"Error generating interactive report: {str(e)}")
            return report_data
    
    def display_streamlit_report(self, results: Dict[str, str], paper_name: str):
        """Display the advanced report in Streamlit with progress tracking"""
        st.header("📊 Advanced Analysis Report")
        st.markdown(f"**Paper:** {paper_name}")
        st.markdown(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Create progress tracking for report generation
        report_progress = st.progress(0)
        report_status = st.empty()
        
        # Step 1: Generate statistics
        report_status.text("📊 Analyzing text statistics...")
        report_progress.progress(20)
        
        # Generate report data
        report_data = self.generate_interactive_report(results, paper_name)
        
        # Step 2: Prepare visualizations
        report_status.text("📈 Creating interactive charts...")
        report_progress.progress(50)
        
        # Display statistics
        if report_data.get('statistics'):
            report_status.text("📋 Processing section metrics...")
            report_progress.progress(70)
            
            st.subheader("📈 Analysis Statistics")
            
            # Create metrics
            total_words = sum(stat['word_count'] for stat in report_data['statistics'].values())
            total_sentences = sum(stat['sentence_count'] for stat in report_data['statistics'].values())
            sections_analyzed = len([k for k, v in results.items() if v and v.strip()])
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Words", f"{total_words:,}")
            with col2:
                st.metric("Total Sentences", f"{total_sentences:,}")
            with col3:
                st.metric("Sections Analyzed", sections_analyzed)
            with col4:
                avg_words_per_section = total_words // sections_analyzed if sections_analyzed > 0 else 0
                st.metric("Avg Words/Section", f"{avg_words_per_section:,}")
        
        # Step 3: Display charts
        report_status.text("🎨 Rendering visualizations...")
        report_progress.progress(85)
        
        # Display charts
        charts = report_data.get('charts', {})
        
        if 'analysis_overview' in charts:
            st.subheader("🎯 Analysis Overview")
            st.plotly_chart(charts['analysis_overview'], use_container_width=True)
        
        if 'keyword_frequency' in charts:
            st.subheader("🏷️ Keyword Frequency Analysis")
            st.plotly_chart(charts['keyword_frequency'], use_container_width=True)
        
        if 'section_analysis' in charts:
            st.subheader("📊 Section-wise Statistics")
            st.plotly_chart(charts['section_analysis'], use_container_width=True)
        
        # Display word cloud
        if report_data.get('wordcloud'):
            st.subheader("☁️ Word Cloud")
            st.markdown("Visual representation of the most frequent terms in your analysis:")
            
            # Decode and display the word cloud
            wordcloud_data = base64.b64decode(report_data['wordcloud'])
            st.image(wordcloud_data, caption="Word Cloud of Analysis Content")
        
        # Detailed statistics table
        if report_data.get('statistics'):
            st.subheader("📋 Detailed Section Statistics")
            
            stats_df = pd.DataFrame(report_data['statistics']).T
            stats_df = stats_df.round(2)
            stats_df.index.name = "Section"
            
            st.dataframe(stats_df, use_container_width=True)
        
        # Export options
        st.subheader("💾 Export Advanced Report")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Prepare data for download
            export_data = {
                'paper_name': paper_name,
                'timestamp': report_data['timestamp'],
                'statistics': report_data['statistics'],
                'analysis_results': results,
                'charts_data': {
                    'total_words': sum(stat['word_count'] for stat in report_data['statistics'].values()) if report_data.get('statistics') else 0,
                    'total_sentences': sum(stat['sentence_count'] for stat in report_data['statistics'].values()) if report_data.get('statistics') else 0,
                    'sections_analyzed': len([k for k, v in results.items() if v and v.strip()]),
                    'sections_completed': list(report_data['statistics'].keys()) if report_data.get('statistics') else []
                }
            }
            
            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
            
            st.download_button(
                label="� Download Report Data (JSON)",
                data=json_str,
                file_name=f"advanced_report_{paper_name.replace('.pdf', '').replace(' ', '_')}.json",
                mime='application/json',
                help="Download complete analysis data including statistics and charts data as JSON"
            )
        
        with col2:
            # Create a comprehensive text report
            text_report = self.create_comprehensive_text_report(results, paper_name, report_data)
            
            st.download_button(
                label="� Download Full Report (TXT)",
                data=text_report,
                file_name=f"comprehensive_report_{paper_name.replace('.pdf', '').replace(' ', '_')}.txt",
                mime='text/plain',
                help="Download a comprehensive text report with all analysis and statistics"
            )
        
        st.success("✅ Advanced report generated successfully!")
    
    def create_comprehensive_text_report(self, results: Dict[str, str], paper_name: str, report_data: Dict[str, Any]) -> str:
        """Create a comprehensive text report with all analysis and statistics"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""
# 📊 ADVANCED AI RESEARCH PAPER ANALYSIS REPORT
# Generated by AI Research Paper Assistant (Powered by Google Gemini)

Paper: {paper_name}
Generated: {timestamp}

{'='*80}
# 📈 ANALYSIS STATISTICS
{'='*80}

"""
        
        # Add statistics if available
        if report_data.get('statistics'):
            total_words = sum(stat['word_count'] for stat in report_data['statistics'].values())
            total_sentences = sum(stat['sentence_count'] for stat in report_data['statistics'].values())
            sections_analyzed = len([k for k, v in results.items() if v and v.strip()])
            avg_words_per_section = total_words // sections_analyzed if sections_analyzed > 0 else 0
            
            report += f"""
OVERVIEW METRICS:
- Total Words: {total_words:,}
- Total Sentences: {total_sentences:,}
- Sections Analyzed: {sections_analyzed}
- Average Words per Section: {avg_words_per_section:,}

DETAILED SECTION STATISTICS:
"""
            
            for section, stats in report_data['statistics'].items():
                report += f"""
{section.upper()}:
  • Word Count: {stats['word_count']:,}
  • Sentence Count: {stats['sentence_count']:,}
  • Character Count: {stats['character_count']:,}
  • Avg Word Length: {stats['avg_word_length']:.1f}
  • Avg Sentence Length: {stats['avg_sentence_length']:.1f} words
"""
        
        # Add the original analysis results
        report += f"""

{'='*80}
# 📝 DETAILED ANALYSIS RESULTS
{'='*80}

"""
        
        # Add each analysis section if it exists
        sections = {
            'summary': '📝 EXECUTIVE SUMMARY',
            'methodology': '🔬 METHODOLOGY ANALYSIS',
            'citations': '📚 CITATIONS & REFERENCES',
            'gaps': '🔍 RESEARCH GAPS IDENTIFIED',
            'keywords': '🏷️ KEY TERMS & CONCEPTS',
            'detailed': '📋 DETAILED ANALYSIS'
        }
        
        for key, title in sections.items():
            if key in results and results[key]:
                report += f"""

## {title}
{'-'*50}

{results[key]}

"""
        
        # Add keyword analysis if we have text
        if any(results.values()):
            all_text = ' '.join([text for text in results.values() if text])
            words = all_text.lower().split()
            
            # Filter out common stop words
            stop_words = {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
                'this', 'that', 'these', 'those', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'
            }
            
            # Count word frequencies
            word_freq = {}
            for word in words:
                clean_word = ''.join(c for c in word if c.isalnum()).lower()
                if len(clean_word) > 3 and clean_word not in stop_words:
                    word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
            
            # Get top 20 words
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
            
            if top_words:
                report += f"""

## 🔢 TOP KEYWORDS FREQUENCY ANALYSIS
{'-'*50}

"""
                for i, (word, freq) in enumerate(top_words, 1):
                    report += f"{i:2}. {word:<20} : {freq:>3} occurrences\n"
        
        report += f"""

{'='*80}
# 📊 REPORT METADATA
{'='*80}

• Report Type: Advanced Interactive Analysis
• AI Model Used: Google Gemini 2.0 Flash
• Analysis Components: {len([k for k, v in results.items() if v and v.strip()])} sections
• Generation Time: {timestamp}
• Tool Version: AI Research Paper Assistant v2.0

{'='*80}

This report was generated by the AI Research Paper Assistant.
For more advanced features, use the interactive web interface.

End of Report
"""
        
        return report

# Example usage
if __name__ == "__main__":
    # Test the report generator
    sample_results = {
        'summary': 'This paper presents a comprehensive analysis of machine learning techniques applied to natural language processing. The study examines various algorithms and their effectiveness in processing textual data.',
        'methodology': 'The research employs a mixed-methods approach combining quantitative analysis with qualitative evaluation. Data collection involves multiple datasets from academic sources.',
        'keywords': 'machine learning, natural language processing, algorithms, data analysis, artificial intelligence'
    }
    
    generator = AdvancedReportGenerator()
    report = generator.generate_interactive_report(sample_results, "test_paper.pdf")
    print("Advanced report generator test completed!")