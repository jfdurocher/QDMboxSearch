#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
MBox Search Tool
---------------
A professional tool for searching through large mbox files.
Author: J.F. Durocher
Copyright (c) 2025 J.F. Durocher (jf@durocher.in)
"""

import os
import sys
import mailbox
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table
import re
from email.utils import parsedate_to_datetime

@dataclass
class EmailMessage:
    """Data class to store email message information."""
    message_id: str
    subject: str
    from_addr: str
    date: datetime
    body: str

class MBoxSearcher:
    """Main class for handling mbox file operations and searching."""
    
    def __init__(self, mbox_path: str):
        """
        Initialize the MBoxSearcher with the path to the mbox file.
        
        Args:
            mbox_path (str): Path to the mbox file
        """
        self.mbox_path = mbox_path
        self.console = Console()
        self.messages: List[EmailMessage] = []
        
    def load_mbox(self) -> None:
        """Load and parse the mbox file with progress indication."""
        if not os.path.exists(self.mbox_path):
            self.console.print(f"[red]Error: File {self.mbox_path} does not exist[/red]")
            sys.exit(1)
            
        try:
            mbox = mailbox.mbox(self.mbox_path)
            total_messages = len(mbox)
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Loading messages...", total=total_messages)
                
                for message in mbox:
                    # Parse the date header safely
                    date_header = message.get('Date', '')
                    date_obj = None
                    if date_header:
                        try:
                            date_obj = parsedate_to_datetime(date_header)
                        except Exception:
                            date_obj = None
                    email = EmailMessage(
                        message_id=message.get('Message-ID', ''),
                        subject=message.get('Subject', ''),
                        from_addr=message.get('From', ''),
                        date=date_obj,
                        body=self._get_message_body(message)
                    )
                    self.messages.append(email)
                    progress.update(task, advance=1)
                    
            self.console.print(f"\n[green]Successfully loaded {len(self.messages)} messages[/green]")
            
        except Exception as e:
            self.console.print(f"[red]Error loading mbox file: {str(e)}[/red]")
            sys.exit(1)
    
    def _get_message_body(self, message) -> str:
        """
        Extract the message body from an email message.
        
        Args:
            message: The email message object
            
        Returns:
            str: The message body text
        """
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body += part.get_payload(decode=True).decode()
                    except:
                        continue
        else:
            try:
                body = message.get_payload(decode=True).decode()
            except:
                body = message.get_payload()
        return body
    
    def search(self, query: str, search_subject: bool = True, search_body: bool = True) -> List[EmailMessage]:
        """
        Search through messages for the given query.
        
        Args:
            query (str): The search query
            search_subject (bool): Whether to search in subject
            search_body (bool): Whether to search in body
            
        Returns:
            List[EmailMessage]: List of matching messages
        """
        query = query.lower()
        results = []
        
        for message in self.messages:
            match = False
            subject = str(message.subject) if not isinstance(message.subject, str) else message.subject
            body = str(message.body) if not isinstance(message.body, str) else message.body
            if search_subject and query in subject.lower():
                match = True
            if search_body and query in body.lower():
                match = True
            if match:
                results.append(message)
                
        return results
    
    def display_results(self, results: List[EmailMessage]) -> None:
        """
        Display search results in a formatted table.
        
        Args:
            results (List[EmailMessage]): List of messages to display
        """
        if not results:
            self.console.print("[yellow]No results found[/yellow]")
            return
            
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Date")
        table.add_column("From")
        table.add_column("Subject")
        
        for message in results:
            date_str = message.date.strftime("%Y-%m-%d %H:%M") if message.date else "Unknown"
            table.add_row(
                date_str,
                message.from_addr,
                message.subject
            )
            
        self.console.print(Panel(table, title="Search Results"))

def main():
    """Main function to run the application."""
    console = Console()
    
    if len(sys.argv) != 2:
        console.print("[red]Usage: python mbox_search.py <path_to_mbox_file>[/red]")
        sys.exit(1)
        
    mbox_path = sys.argv[1]
    searcher = MBoxSearcher(mbox_path)
    
    try:
        searcher.load_mbox()
        
        while True:
            console.print("\n[bold blue]MBox Search Tool[/bold blue]")
            console.print("1. Search in subject")
            console.print("2. Search in body")
            console.print("3. Search in both")
            console.print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ")
            
            if choice == '4':
                break
                
            if choice not in ['1', '2', '3']:
                console.print("[red]Invalid choice. Please try again.[/red]")
                continue
                
            query = input("Enter search query: ")
            if not query:
                console.print("[yellow]Empty query. Please try again.[/yellow]")
                continue
                
            search_subject = choice in ['1', '3']
            search_body = choice in ['2', '3']
            
            results = searcher.search(query, search_subject, search_body)
            searcher.display_results(results)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Search interrupted by user[/yellow]")
    except Exception as e:
        console.print(f"[red]An error occurred: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 