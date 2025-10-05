import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import os
import sys
import json
import threading
import time
from pathlib import Path
import re

# Add the transpiler to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from transpiler import PythonToJavaScriptTranspiler
    from transpiler.errors import TranspilerError
except ImportError as e:
    # Create a mock transpiler for testing
    class TranspilerError(Exception):
        pass
    
    class PythonToJavaScriptTranspiler:
        def transpile(self, code):
            # Simple mock transpilation for demo
            lines = code.strip().split('\n')
            js_lines = []
            js_lines.append("// Generated JavaScript")
            js_lines.append("")
            
            for line in lines:
                line = line.strip()
                if line.startswith('def '):
                    # Convert function definition
                    func_match = re.match(r'def\s+(\w+)\s*\(([^)]*)\)\s*:', line)
                    if func_match:
                        func_name, params = func_match.groups()
                        js_lines.append(f"function {func_name}({params}) {{")
                elif line.startswith('return '):
                    # Convert return statement
                    value = line[7:]
                    js_lines.append(f"    return {value};")
                elif line.startswith('print('):
                    # Convert print to console.log
                    args = line[6:-1]
                    js_lines.append(f"console.log({args});")
                elif '=' in line and not line.startswith('if') and not line.startswith('while'):
                    # Convert assignment
                    if '+=' in line:
                        js_lines.append(f"{line};")
                    else:
                        parts = line.split('=', 1)
                        js_lines.append(f"let {parts[0].strip()} = {parts[1].strip()};")
                elif line.startswith('if '):
                    # Convert if statement
                    condition = line[3:-1]
                    js_lines.append(f"if ({condition}) {{")
                elif line == 'else:':
                    js_lines.append("} else {")
                elif line.startswith('for '):
                    # Convert for loop
                    js_lines.append(f"// {line}")
                elif line.startswith('while '):
                    # Convert while loop
                    condition = line[6:-1]
                    js_lines.append(f"while ({condition}) {{")
                elif line and not line.startswith('#'):
                    # Other statements
                    js_lines.append(f"{line};")
                elif line.startswith('#'):
                    # Comments
                    js_lines.append(f"// {line[1:]}")
            
            # Close any open braces
            js_lines.append("}")
            
            return '\n'.join(js_lines)


class ModernTranspilerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🐍➡️⚡ Python to JavaScript Transpiler")
        self.root.geometry("1400x900")
        self.root.minsize(1000, 700)
        
        # Initialize application state FIRST (before setup_styles)
        self.current_python_file = None
        self.current_js_file = None
        self.is_modified = False
        self.auto_transpile_enabled = tk.BooleanVar(value=True)
        self.current_theme = tk.StringVar(value="dark")
        self.font_size = tk.IntVar(value=12)
        self.auto_transpile_timer = None
        self.recent_files = []
        self.max_recent_files = 10
        
        # Now configure modern styling
        self.setup_styles()
        
        # Initialize transpiler
        self.transpiler = PythonToJavaScriptTranspiler()
        
        # Create GUI components
        self.create_menu_bar()
        self.create_toolbar()
        self.create_main_interface()
        self.create_status_bar()
        self.setup_keyboard_shortcuts()
        
        # Apply initial theme and settings
        self.apply_theme()
        self.load_welcome_code()
        self.setup_auto_transpile()
        
        # Load settings
        self.load_settings()
    
    def setup_styles(self):
        """Configure modern styling for the application"""
        self.style = ttk.Style()
        
        # Use a modern theme
        available_themes = self.style.theme_names()
        modern_themes = ['vista', 'xpnative', 'winnative', 'clam']
        for theme in modern_themes:
            if theme in available_themes:
                self.style.theme_use(theme)
                break
        
        # Define color schemes
        self.colors = {
            'dark': {
                'bg': '#2b2b2b',
                'fg': '#ffffff',
                'editor_bg': '#1e1e1e',
                'editor_fg': '#d4d4d4',
                'js_bg': '#0f1419',
                'js_fg': '#bfbdb6',
                'error_bg': '#2d1b1b',
                'error_fg': '#ffcccb',
                'accent': '#007acc',
                'button_bg': '#3c3c3c',
                'select_bg': '#264f78'
            },
            'light': {
                'bg': '#ffffff',
                'fg': '#000000',
                'editor_bg': '#ffffff',
                'editor_fg': '#000000',
                'js_bg': '#f8f8f8',
                'js_fg': '#333333',
                'error_bg': '#fff8f8',
                'error_fg': '#d32f2f',
                'accent': '#0066cc',
                'button_bg': '#f0f0f0',
                'select_bg': '#cce8ff'
            }
        }
        
        # Configure custom styles
        self.configure_custom_styles()
    
    def configure_custom_styles(self):
        """Configure custom ttk styles"""
        # Use default theme initially if current_theme not set
        if hasattr(self, 'current_theme'):
            theme = self.current_theme.get()
        else:
            theme = 'dark'  # Default to dark theme
            
        colors = self.colors[theme]
        
        # Modern frame style
        self.style.configure('Modern.TFrame', background=colors['bg'])
        
        # Modern label style
        self.style.configure('Modern.TLabel', 
                           background=colors['bg'], 
                           foreground=colors['fg'],
                           font=('Segoe UI', 10))
        
        # Accent button style
        self.style.configure('Accent.TButton',
                           background=colors['accent'],
                           foreground='white',
                           font=('Segoe UI', 9, 'bold'),
                           padding=(15, 8))
        
        # Modern button style
        self.style.configure('Modern.TButton',
                           font=('Segoe UI', 9),
                           padding=(12, 6))
        
        # Toolbar style
        self.style.configure('Toolbar.TFrame',
                           background=colors['button_bg'],
                           relief='flat',
                           borderwidth=1)

    def create_menu_bar(self):
        """Create the application menu bar"""
        colors = self.colors[self.current_theme.get()]
        
        self.menubar = tk.Menu(self.root, 
                              bg=colors['bg'],
                              fg=colors['fg'],
                              activebackground=colors['accent'])
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0,
                           bg=colors['button_bg'],
                           fg=colors['fg'],
                           activebackground=colors['accent'])
        self.menubar.add_cascade(label="📁 File", menu=file_menu)
        file_menu.add_command(label="🆕 New", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="📂 Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="💾 Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="💾 Save As...", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_command(label="📤 Export JavaScript...", command=self.export_javascript)
        file_menu.add_separator()
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0,
                                  bg=colors['button_bg'],
                                  fg=colors['fg'])
        file_menu.add_cascade(label="🕒 Recent Files", menu=self.recent_menu)
        
        file_menu.add_separator()
        file_menu.add_command(label="🚪 Exit", command=self.exit_application)
        
        # Edit menu
        edit_menu = tk.Menu(self.menubar, tearoff=0,
                           bg=colors['button_bg'],
                           fg=colors['fg'],
                           activebackground=colors['accent'])
        self.menubar.add_cascade(label="✏️ Edit", menu=edit_menu)
        edit_menu.add_command(label="↶ Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="↷ Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="✂️ Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="📋 Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="📄 Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="🔘 Select All", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="🔍 Find", command=self.find_text, accelerator="Ctrl+F")
        
        # Tools menu
        tools_menu = tk.Menu(self.menubar, tearoff=0,
                            bg=colors['button_bg'],
                            fg=colors['fg'],
                            activebackground=colors['accent'])
        self.menubar.add_cascade(label="🛠️ Tools", menu=tools_menu)
        tools_menu.add_command(label="🚀 Transpile Now", command=self.transpile_now, accelerator="F5")
        tools_menu.add_checkbutton(label="⚡ Auto-transpile", variable=self.auto_transpile_enabled)
        tools_menu.add_separator()
        tools_menu.add_command(label="🗑️ Clear Output", command=self.clear_output)
        tools_menu.add_command(label="📋 Copy JavaScript", command=self.copy_javascript)
        
        # Samples menu
        samples_menu = tk.Menu(self.menubar, tearoff=0,
                              bg=colors['button_bg'],
                              fg=colors['fg'],
                              activebackground=colors['accent'])
        self.menubar.add_cascade(label="📚 Samples", menu=samples_menu)
        samples_menu.add_command(label="👋 Welcome", command=lambda: self.load_sample("welcome"))
        samples_menu.add_command(label="🔢 Factorial", command=lambda: self.load_sample("factorial"))
        samples_menu.add_command(label="🔢 Fibonacci", command=lambda: self.load_sample("fibonacci"))
        samples_menu.add_command(label="📝 Lists", command=lambda: self.load_sample("lists"))
        samples_menu.add_command(label="🔄 Control Flow", command=lambda: self.load_sample("control"))
        samples_menu.add_command(label="⚙️ Functions", command=lambda: self.load_sample("functions"))
        
        # View menu
        view_menu = tk.Menu(self.menubar, tearoff=0,
                           bg=colors['button_bg'],
                           fg=colors['fg'],
                           activebackground=colors['accent'])
        self.menubar.add_cascade(label="👁️ View", menu=view_menu)
        view_menu.add_checkbutton(label="🌙 Dark Theme", 
                                 variable=self.current_theme,
                                 onvalue="dark", offvalue="light",
                                 command=self.toggle_theme)
        view_menu.add_separator()
        view_menu.add_command(label="🔍+ Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        view_menu.add_command(label="🔍- Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        view_menu.add_command(label="🔍 Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0,
                           bg=colors['button_bg'],
                           fg=colors['fg'],
                           activebackground=colors['accent'])
        self.menubar.add_cascade(label="❓ Help", menu=help_menu)
        help_menu.add_command(label="📖 Language Guide", command=self.show_language_guide)
        help_menu.add_command(label="⌨️ Shortcuts", command=self.show_shortcuts)
        help_menu.add_separator()
        help_menu.add_command(label="ℹ️ About", command=self.show_about)

    def create_toolbar(self):
        """Create the modern toolbar"""
        # Main toolbar frame
        self.toolbar = ttk.Frame(self.root, style='Toolbar.TFrame', padding=(10, 8))
        self.toolbar.pack(side=tk.TOP, fill=tk.X)
        
        # File operations section
        file_frame = ttk.Frame(self.toolbar)
        file_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(file_frame, text="🆕 New", command=self.new_file, 
                  style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="📂 Open", command=self.open_file,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(file_frame, text="💾 Save", command=self.save_file,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 5))
        
        # Separator
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=(10, 15))
        
        # Transpile section
        transpile_frame = ttk.Frame(self.toolbar)
        transpile_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        # Main transpile button (prominent)
        self.transpile_btn = ttk.Button(transpile_frame, text="🚀 Transpile", 
                                       command=self.transpile_now, 
                                       style='Accent.TButton')
        self.transpile_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Auto-transpile checkbox
        ttk.Checkbutton(transpile_frame, text="⚡ Auto", 
                       variable=self.auto_transpile_enabled).pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(self.toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=(10, 15))
        
        # View controls section
        view_frame = ttk.Frame(self.toolbar)
        view_frame.pack(side=tk.LEFT, padx=(0, 15))
        
        ttk.Button(view_frame, text="🌙 Theme", command=self.toggle_theme,
                  style='Modern.TButton').pack(side=tk.LEFT, padx=(0, 10))
        
        # Font size controls
        font_frame = ttk.Frame(view_frame)
        font_frame.pack(side=tk.LEFT)
        
        ttk.Label(font_frame, text="Font:", style='Modern.TLabel').pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(font_frame, text="−", command=self.zoom_out, width=3,
                  style='Modern.TButton').pack(side=tk.LEFT)
        
        self.font_label = ttk.Label(font_frame, textvariable=self.font_size, 
                                   width=3, style='Modern.TLabel')
        self.font_label.pack(side=tk.LEFT, padx=(3, 3))
        
        ttk.Button(font_frame, text="+", command=self.zoom_in, width=3,
                  style='Modern.TButton').pack(side=tk.LEFT)
        
        # Right side tools
        right_frame = ttk.Frame(self.toolbar)
        right_frame.pack(side=tk.RIGHT)
        
        ttk.Button(right_frame, text="📋 Copy JS", command=self.copy_javascript,
                  style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(right_frame, text="🗑️ Clear", command=self.clear_output,
                  style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))

    def create_main_interface(self):
        """Create the main split-pane interface"""
        # Main container with padding
        main_container = ttk.Frame(self.root, style='Modern.TFrame', padding=(10, 5))
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Horizontal paned window for main split
        self.main_paned = ttk.PanedWindow(main_container, orient=tk.HORIZONTAL)
        self.main_paned.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Python input
        self.create_python_panel()
        
        # Right panel - JavaScript output and messages
        self.create_output_panel()
        
        # Set initial pane weights
        self.main_paned.add(self.left_panel, weight=1)
        self.main_paned.add(self.right_panel, weight=1)

    def create_python_panel(self):
        """Create the Python code input panel"""
        self.left_panel = ttk.Frame(self.main_paned, style='Modern.TFrame')
        
        # Header with title and stats
        header_frame = ttk.Frame(self.left_panel, style='Modern.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 8))
        
        # Title and icon
        title_frame = ttk.Frame(header_frame)
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="🐍", font=('Segoe UI', 16)).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="Python Code", 
                 font=('Segoe UI', 14, 'bold'),
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=(5, 0))
        
        # Stats on the right
        stats_frame = ttk.Frame(header_frame)
        stats_frame.pack(side=tk.RIGHT)
        
        self.line_count_label = ttk.Label(stats_frame, text="Lines: 0", 
                                         style='Modern.TLabel')
        self.line_count_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        self.char_count_label = ttk.Label(stats_frame, text="Chars: 0", 
                                         style='Modern.TLabel')
        self.char_count_label.pack(side=tk.RIGHT)
        
        # Editor container with line numbers
        editor_container = ttk.Frame(self.left_panel)
        editor_container.pack(fill=tk.BOTH, expand=True)
        
        # Line numbers frame
        line_frame = ttk.Frame(editor_container)
        line_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        self.line_numbers = tk.Text(
            line_frame,
            width=4,
            padx=8,
            pady=10,
            takefocus=0,
            border=0,
            state='disabled',
            wrap='none',
            background='#3c3c3c',
            foreground='#888888',
            font=('Consolas', self.font_size.get()),
            cursor="arrow"
        )
        self.line_numbers.pack(side=tk.LEFT, fill=tk.Y)
        
        # Main Python editor
        editor_frame = ttk.Frame(editor_container)
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.python_editor = tk.Text(
            editor_frame,
            wrap=tk.NONE,
            undo=True,
            maxundo=100,
            font=('Consolas', self.font_size.get()),
            background='#1e1e1e',
            foreground='#d4d4d4',
            insertbackground='#ffffff',
            selectbackground='#264f78',
            selectforeground='#ffffff',
            tabs=('1c', '2c', '3c', '4c'),
            padx=15,
            pady=10,
            borderwidth=0,
            highlightthickness=0
        )
        self.python_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars for Python editor
        py_scroll_y = ttk.Scrollbar(editor_frame, orient=tk.VERTICAL, 
                                   command=self.sync_scroll_y)
        py_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.python_editor.config(yscrollcommand=py_scroll_y.set)
        
        py_scroll_x = ttk.Scrollbar(self.left_panel, orient=tk.HORIZONTAL,
                                   command=self.python_editor.xview)
        py_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.python_editor.config(xscrollcommand=py_scroll_x.set)
        
        # Sync line numbers scrolling
        self.line_numbers.config(yscrollcommand=self.sync_line_scroll)

    def create_output_panel(self):
        """Create the JavaScript output and messages panel"""
        self.right_panel = ttk.Frame(self.main_paned, style='Modern.TFrame')
        
        # Vertical paned window for output sections
        output_paned = ttk.PanedWindow(self.right_panel, orient=tk.VERTICAL)
        output_paned.pack(fill=tk.BOTH, expand=True)
        
        # JavaScript output section
        self.create_javascript_section(output_paned)
        
        # Messages and errors section
        self.create_messages_section(output_paned)

    def create_javascript_section(self, parent):
        """Create the JavaScript output section"""
        js_frame = ttk.Frame(parent, style='Modern.TFrame')
        parent.add(js_frame, weight=3)
        
        # Header
        js_header = ttk.Frame(js_frame, style='Modern.TFrame')
        js_header.pack(fill=tk.X, pady=(0, 8))
        
        # Title
        title_frame = ttk.Frame(js_header)
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="⚡", font=('Segoe UI', 16)).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="Generated JavaScript", 
                 font=('Segoe UI', 14, 'bold'),
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=(5, 0))
        
        # Controls
        controls_frame = ttk.Frame(js_header)
        controls_frame.pack(side=tk.RIGHT)
        
        ttk.Button(controls_frame, text="📋 Copy", command=self.copy_javascript,
                  style='Modern.TButton').pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(controls_frame, text="💾 Save", command=self.export_javascript,
                  style='Modern.TButton').pack(side=tk.RIGHT)
        
        # JavaScript editor
        js_editor_frame = ttk.Frame(js_frame)
        js_editor_frame.pack(fill=tk.BOTH, expand=True)
        
        self.js_editor = tk.Text(
            js_editor_frame,
            wrap=tk.NONE,
            state=tk.DISABLED,
            font=('Consolas', self.font_size.get()),
            background='#0f1419',
            foreground='#bfbdb6',
            tabs=('1c', '2c', '3c', '4c'),
            padx=15,
            pady=10,
            borderwidth=0,
            highlightthickness=0
        )
        self.js_editor.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Scrollbars for JavaScript editor
        js_scroll_y = ttk.Scrollbar(js_editor_frame, orient=tk.VERTICAL,
                                   command=self.js_editor.yview)
        js_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.js_editor.config(yscrollcommand=js_scroll_y.set)
        
        js_scroll_x = ttk.Scrollbar(js_frame, orient=tk.HORIZONTAL,
                                   command=self.js_editor.xview)
        js_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self.js_editor.config(xscrollcommand=js_scroll_x.set)

    def create_messages_section(self, parent):
        """Create the messages and errors section"""
        msg_frame = ttk.Frame(parent, style='Modern.TFrame')
        parent.add(msg_frame, weight=1)
        
        # Header
        msg_header = ttk.Frame(msg_frame, style='Modern.TFrame')
        msg_header.pack(fill=tk.X, pady=(0, 8))
        
        # Title
        title_frame = ttk.Frame(msg_header)
        title_frame.pack(side=tk.LEFT)
        
        ttk.Label(title_frame, text="💬", font=('Segoe UI', 16)).pack(side=tk.LEFT)
        ttk.Label(title_frame, text="Messages & Status", 
                 font=('Segoe UI', 14, 'bold'),
                 style='Modern.TLabel').pack(side=tk.LEFT, padx=(5, 0))
        
        # Status indicator
        self.status_indicator = ttk.Label(msg_header, text="⚪ Ready", 
                                         style='Modern.TLabel')
        self.status_indicator.pack(side=tk.RIGHT)
        
        # Messages text area
        self.messages_text = scrolledtext.ScrolledText(
            msg_frame,
            wrap=tk.WORD,
            state=tk.DISABLED,
            font=('Consolas', 10),
            background='#2d1b1b',
            foreground='#ffcccb',
            height=8,
            borderwidth=0,
            highlightthickness=0,
            padx=10,
            pady=8
        )
        self.messages_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for different message types
        self.messages_text.tag_configure('success', foreground='#90EE90')
        self.messages_text.tag_configure('error', foreground='#FF6B6B')
        self.messages_text.tag_configure('warning', foreground='#FFD93D')
        self.messages_text.tag_configure('info', foreground='#6BCF7F')

    def create_status_bar(self):
        """Create the status bar at the bottom"""
        self.status_frame = ttk.Frame(self.root, style='Toolbar.TFrame', padding=(10, 5))
        self.status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # File status
        self.file_status_label = ttk.Label(self.status_frame, text="Ready", 
                                          style='Modern.TLabel')
        self.file_status_label.pack(side=tk.LEFT)
        
        # Separator
        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=(15, 15))
        
        # Transpilation status
        self.transpile_status_label = ttk.Label(self.status_frame, text="", 
                                               style='Modern.TLabel')
        self.transpile_status_label.pack(side=tk.LEFT)
        
        # Right side - cursor position
        self.cursor_label = ttk.Label(self.status_frame, text="Ln: 1, Col: 1", 
                                     style='Modern.TLabel')
        self.cursor_label.pack(side=tk.RIGHT)
        
        # Word count
        ttk.Separator(self.status_frame, orient=tk.VERTICAL).pack(side=tk.RIGHT, fill=tk.Y, padx=(15, 15))
        
        self.word_count_label = ttk.Label(self.status_frame, text="Words: 0", 
                                         style='Modern.TLabel')
        self.word_count_label.pack(side=tk.RIGHT)

    def setup_keyboard_shortcuts(self):
        """Setup keyboard shortcuts"""
        shortcuts = {
            '<Control-n>': lambda e: self.new_file(),
            '<Control-o>': lambda e: self.open_file(),
            '<Control-s>': lambda e: self.save_file(),
            '<Control-Shift-S>': lambda e: self.save_as_file(),
            '<Control-z>': lambda e: self.undo(),
            '<Control-y>': lambda e: self.redo(),
            '<Control-x>': lambda e: self.cut(),
            '<Control-c>': lambda e: self.copy(),
            '<Control-v>': lambda e: self.paste(),
            '<Control-a>': lambda e: self.select_all(),
            '<Control-f>': lambda e: self.find_text(),
            '<F5>': lambda e: self.transpile_now(),
            '<Control-plus>': lambda e: self.zoom_in(),
            '<Control-minus>': lambda e: self.zoom_out(),
            '<Control-0>': lambda e: self.reset_zoom(),
            '<Control-q>': lambda e: self.exit_application(),
        }
        
        for shortcut, command in shortcuts.items():
            self.root.bind(shortcut, command)

    def setup_auto_transpile(self):
        """Setup auto-transpile functionality"""
        self.python_editor.bind('<KeyRelease>', self.on_text_change)
        self.python_editor.bind('<Button-1>', self.on_cursor_change)
        self.python_editor.bind('<KeyRelease>', self.on_cursor_change, add='+')
        
        # Initial update
        self.update_line_numbers()
        self.update_statistics()

    def apply_theme(self):
        """Apply the current theme to all components"""
        theme = self.current_theme.get()
        colors = self.colors[theme]
        
        # Update root window
        self.root.configure(bg=colors['bg'])
        
        # Update editors if they exist
        if hasattr(self, 'python_editor'):
            self.python_editor.configure(
                bg=colors['editor_bg'],
                fg=colors['editor_fg'],
                selectbackground=colors['select_bg']
            )
            
            self.js_editor.configure(
                bg=colors['js_bg'],
                fg=colors['js_fg']
            )
            
            self.messages_text.configure(
                bg=colors['error_bg'],
                fg=colors['error_fg']
            )
            
            self.line_numbers.configure(
                bg=colors['button_bg'],
                fg='#888888'
            )
        
        # Update menu colors
        if hasattr(self, 'menubar'):
            self.menubar.configure(
                bg=colors['bg'],
                fg=colors['fg'],
                activebackground=colors['accent']
            )
        
        # Reconfigure custom styles
        self.configure_custom_styles()

    def load_welcome_code(self):
        """Load welcome code to demonstrate features"""
        welcome_code = """# 🎉 Welcome to Python → JavaScript Transpiler! 🎉
# This modern tool converts Python-like code to JavaScript

def greet(name):
    return "Hello, " + name + "! 👋"

def calculate_factorial(n):
    if n <= 1:
        return 1
    else:
        return n * calculate_factorial(n - 1)

def process_numbers(numbers):
    total = 0
    evens = []
    
    for num in numbers:
        total += num
        if num % 2 == 0:
            evens.append(num)
    
    return total, evens

# 🚀 Demo Usage
message = greet("Developer")
print(message)

# Calculate factorial of 5
factorial_result = calculate_factorial(5)
print("Factorial of 5:", factorial_result)

# Process some numbers
test_numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
sum_result, even_numbers = process_numbers(test_numbers)

print("Sum of all numbers:", sum_result)
print("Even numbers:", even_numbers)

# 🎯 Try the features:
# - Auto-transpile is enabled by default
# - Use Ctrl+S to save your code
# - Check the Samples menu for more examples
# - Press F5 to manually transpile
# - Use Ctrl+F to find text"""
        
        self.python_editor.delete(1.0, tk.END)
        self.python_editor.insert(1.0, welcome_code)
        self.update_line_numbers()
        self.update_statistics()
        
        # Initial transpile
        if self.auto_transpile_enabled.get():
            self.root.after(1000, self.auto_transpile)

    def on_text_change(self, event=None):
        """Handle text changes for auto-transpile and updates"""
        self.is_modified = True
        self.update_line_numbers()
        self.update_statistics()
        self.update_status()
        
        if self.auto_transpile_enabled.get():
            self.schedule_auto_transpile()

    def on_cursor_change(self, event=None):
        """Handle cursor position changes"""
        self.update_cursor_position()

    def schedule_auto_transpile(self):
        """Schedule auto-transpilation with delay"""
        if self.auto_transpile_timer:
            self.root.after_cancel(self.auto_transpile_timer)
        self.auto_transpile_timer = self.root.after(1500, self.auto_transpile)

    def auto_transpile(self):
        """Perform automatic transpilation"""
        if self.auto_transpile_enabled.get():
            self.transpile_code(is_auto=True)

    def sync_scroll_y(self, *args):
        """Synchronize vertical scrolling between editor and line numbers"""
        self.python_editor.yview(*args)
        self.line_numbers.yview(*args)

    def sync_line_scroll(self, *args):
        """Synchronize line numbers scrolling"""
        # This prevents the line numbers from scrolling independently
        pass

    def update_line_numbers(self):
        """Update the line numbers display"""
        if not hasattr(self, 'line_numbers'):
            return
        
        # Get the content and count lines
        content = self.python_editor.get(1.0, tk.END)
        lines = content.count('\n')
        
        # Update line numbers
        self.line_numbers.config(state='normal')
        self.line_numbers.delete(1.0, tk.END)
        
        for i in range(1, lines + 1):
            self.line_numbers.insert(tk.END, f"{i:>3}\n")
        
        self.line_numbers.config(state='disabled')
        
        # Update line count display
        self.line_count_label.config(text=f"Lines: {lines}")

    def update_statistics(self):
        """Update character and word counts"""
        content = self.python_editor.get(1.0, tk.END)
        char_count = len(content) - 1  # Subtract trailing newline
        word_count = len([word for word in content.split() if word.strip()])
        
        self.char_count_label.config(text=f"Chars: {char_count}")
        self.word_count_label.config(text=f"Words: {word_count}")

    def update_cursor_position(self):
        """Update cursor position display"""
        try:
            cursor_pos = self.python_editor.index(tk.INSERT)
            line, col = cursor_pos.split('.')
            self.cursor_label.config(text=f"Ln: {line}, Col: {int(col)+1}")
        except:
            pass

    def update_status(self):
        """Update file status display"""
        if self.current_python_file:
            filename = os.path.basename(self.current_python_file)
            status = f"{filename}{'*' if self.is_modified else ''}"
        else:
            status = f"Untitled{'*' if self.is_modified else ''}"
        
        self.file_status_label.config(text=status)

    def add_message(self, message, msg_type='info'):
        """Add a message to the messages panel"""
        self.messages_text.config(state=tk.NORMAL)
        
        # Add timestamp
        import datetime
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Add the message with appropriate styling
        self.messages_text.insert(tk.END, f"[{timestamp}] ", 'info')
        self.messages_text.insert(tk.END, f"{message}\n", msg_type)
        
        # Auto-scroll to bottom
        self.messages_text.see(tk.END)
        self.messages_text.config(state=tk.DISABLED)

    # Transpilation methods
    def transpile_now(self):
        """Force immediate transpilation"""
        self.transpile_code(is_auto=False)

    def transpile_code(self, is_auto=False):
        """Transpile Python code to JavaScript"""
        python_code = self.python_editor.get(1.0, tk.END).strip()
        
        if not python_code:
            self.clear_output()
            self.status_indicator.config(text="⚪ Ready")
            self.transpile_status_label.config(text="No code to transpile")
            return
        
        try:
            # Update status
            self.status_indicator.config(text="🟡 Transpiling...")
            self.root.update_idletasks()
            
            # Clear previous output
            self.js_editor.config(state=tk.NORMAL)
            self.js_editor.delete(1.0, tk.END)
            
            # Perform transpilation
            js_code = self.transpiler.transpile(python_code)
            
            # Display result with syntax highlighting
            self.js_editor.insert(1.0, js_code)
            self.highlight_javascript()
            self.js_editor.config(state=tk.DISABLED)
            
            # Update status
            self.status_indicator.config(text="🟢 Success")
            
            # Add success message
            mode = "Auto-transpiled" if is_auto else "Transpiled"
            lines = len(js_code.split('\n'))
            self.add_message(f"✅ {mode} successfully! Generated {lines} lines of JavaScript.", 'success')
            
            self.transpile_status_label.config(text=f"{mode} successfully")
            
        except TranspilerError as e:
            # Handle transpilation errors
            self.js_editor.config(state=tk.DISABLED)
            self.status_indicator.config(text="🔴 Error")
            
            error_msg = f"❌ Transpilation Error: {str(e)}"
            self.add_message(error_msg, 'error')
            
            self.transpile_status_label.config(text="Transpilation failed")
            
        except Exception as e:
            # Handle unexpected errors
            self.js_editor.config(state=tk.DISABLED)
            self.status_indicator.config(text="🔴 Error")
            
            error_msg = f"💥 Unexpected Error: {str(e)}"
            self.add_message(error_msg, 'error')
            
            self.transpile_status_label.config(text="Unexpected error")

    def highlight_javascript(self):
        """Apply basic syntax highlighting to JavaScript"""
        # Configure syntax highlighting tags
        self.js_editor.tag_configure('js_keyword', foreground='#569cd6')
        self.js_editor.tag_configure('js_string', foreground='#ce9178')
        self.js_editor.tag_configure('js_comment', foreground='#6a9955')
        self.js_editor.tag_configure('js_number', foreground='#b5cea8')
        self.js_editor.tag_configure('js_function', foreground='#dcdcaa')
        
        content = self.js_editor.get(1.0, tk.END)
        
        # JavaScript keywords
        js_keywords = [
            'function', 'var', 'let', 'const', 'if', 'else', 'for', 'while',
            'return', 'true', 'false', 'null', 'undefined', 'console', 'log'
        ]
        
        # Highlight keywords
        for keyword in js_keywords:
            start = '1.0'
            while True:
                pos = self.js_editor.search(f'\\b{keyword}\\b', start, tk.END, regexp=True)
                if not pos:
                    break
                end_pos = f"{pos}+{len(keyword)}c"
                self.js_editor.tag_add('js_keyword', pos, end_pos)
                start = end_pos
        
        # Highlight strings (simple approach)
        start = '1.0'
        while True:
            pos = self.js_editor.search('"', start, tk.END)
            if not pos:
                break
            # Find closing quote
            end_pos = self.js_editor.search('"', f"{pos}+1c", tk.END)
            if end_pos:
                self.js_editor.tag_add('js_string', pos, f"{end_pos}+1c")
                start = f"{end_pos}+1c"
            else:
                break
        
        # Highlight comments
        start = '1.0'
        while True:
            pos = self.js_editor.search('//', start, tk.END)
            if not pos:
                break
            end_pos = self.js_editor.search('\\n', pos, tk.END, regexp=True)
            if not end_pos:
                end_pos = tk.END
            self.js_editor.tag_add('js_comment', pos, end_pos)
            start = end_pos

    # File operations
    def new_file(self):
        """Create a new file"""
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes", 
                "You have unsaved changes. Save before creating a new file?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes, save first
                if not self.save_file():
                    return
        
        self.python_editor.delete(1.0, tk.END)
        self.clear_output()
        self.current_python_file = None
        self.is_modified = False
        self.update_status()
        self.update_line_numbers()
        self.update_statistics()
        
        self.add_message("📄 New file created", 'info')
        self.transpile_status_label.config(text="New file ready")

    def open_file(self):
        """Open a Python file"""
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "Unsaved Changes",
                "You have unsaved changes. Save before opening a new file?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes, save first
                if not self.save_file():
                    return
        
        filename = filedialog.askopenfilename(
            title="Open Python File",
            filetypes=[
                ("Python files", "*.py"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.python_editor.delete(1.0, tk.END)
                self.python_editor.insert(1.0, content)
                
                self.current_python_file = filename
                self.is_modified = False
                self.add_to_recent_files(filename)
                
                self.update_status()
                self.update_line_numbers()
                self.update_statistics()
                
                # Auto-transpile if enabled
                if self.auto_transpile_enabled.get():
                    self.schedule_auto_transpile()
                
                basename = os.path.basename(filename)
                self.add_message(f"📂 Opened: {basename}", 'success')
                self.transpile_status_label.config(text=f"Opened: {basename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\n{e}")

    def save_file(self):
        """Save the current file"""
        if self.current_python_file:
            return self.save_to_file(self.current_python_file)
        else:
            return self.save_as_file()

    def save_as_file(self):
        """Save file with new name"""
        filename = filedialog.asksaveasfilename(
            title="Save Python File",
            defaultextension=".py",
            filetypes=[
                ("Python files", "*.py"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            if self.save_to_file(filename):
                self.current_python_file = filename
                self.add_to_recent_files(filename)
                return True
        return False

    def save_to_file(self, filename):
        """Save content to specified file"""
        try:
            content = self.python_editor.get(1.0, tk.END)
            # Remove trailing newline that tkinter adds
            if content.endswith('\n'):
                content = content[:-1]
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(content)
            
            self.is_modified = False
            self.update_status()
            
            basename = os.path.basename(filename)
            self.add_message(f"💾 Saved: {basename}", 'success')
            self.transpile_status_label.config(text=f"Saved: {basename}")
            
            return True
            
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")
            return False

    def export_javascript(self):
        """Export JavaScript to file"""
        js_content = self.js_editor.get(1.0, tk.END).strip()
        if not js_content:
            messagebox.showwarning("Warning", "No JavaScript code to export!")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Export JavaScript File",
            defaultextension=".js",
            filetypes=[
                ("JavaScript files", "*.js"),
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(js_content)
                
                basename = os.path.basename(filename)
                self.add_message(f"📤 JavaScript exported: {basename}", 'success')
                self.transpile_status_label.config(text=f"Exported: {basename}")
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not export JavaScript:\n{e}")

    # Edit operations
    def undo(self):
        """Undo last operation"""
        try:
            self.python_editor.edit_undo()
        except tk.TclError:
            pass

    def redo(self):
        """Redo last undone operation"""
        try:
            self.python_editor.edit_redo()
        except tk.TclError:
            pass

    def cut(self):
        """Cut selected text"""
        try:
            self.python_editor.event_generate("<<Cut>>")
        except tk.TclError:
            pass

    def copy(self):
        """Copy selected text"""
        try:
            self.python_editor.event_generate("<<Copy>>")
        except tk.TclError:
            pass

    def paste(self):
        """Paste text from clipboard"""
        try:
            self.python_editor.event_generate("<<Paste>>")
        except tk.TclError:
            pass

    def select_all(self):
        """Select all text in Python editor"""
        self.python_editor.tag_add(tk.SEL, "1.0", tk.END)
        self.python_editor.mark_set(tk.INSERT, "1.0")
        self.python_editor.see(tk.INSERT)

    def find_text(self):
        """Open find dialog"""
        search_term = simpledialog.askstring("Find", "Enter text to find:")
        if search_term:
            self.highlight_search_term(search_term)

    def highlight_search_term(self, term):
        """Highlight search term in editor"""
        # Remove previous highlights
        self.python_editor.tag_remove('search', '1.0', tk.END)
        
        # Configure highlight tag
        self.python_editor.tag_configure('search', background='yellow', foreground='black')
        
        # Find and highlight all occurrences
        start = '1.0'
        count = 0
        while True:
            pos = self.python_editor.search(term, start, tk.END, nocase=True)
            if not pos:
                break
            end_pos = f"{pos}+{len(term)}c"
            self.python_editor.tag_add('search', pos, end_pos)
            start = end_pos
            count += 1
        
        if count > 0:
            self.add_message(f"🔍 Found {count} occurrences of '{term}'", 'info')
        else:
            self.add_message(f"🔍 No occurrences of '{term}' found", 'warning')

    # Tool operations
    def clear_output(self):
        """Clear all output"""
        self.js_editor.config(state=tk.NORMAL)
        self.js_editor.delete(1.0, tk.END)
        self.js_editor.config(state=tk.DISABLED)
        
        self.messages_text.config(state=tk.NORMAL)
        self.messages_text.delete(1.0, tk.END)
        self.messages_text.config(state=tk.DISABLED)
        
        self.status_indicator.config(text="⚪ Ready")
        self.transpile_status_label.config(text="Output cleared")
        
        self.add_message("🗑️ Output cleared", 'info')

    def copy_javascript(self):
        """Copy JavaScript to clipboard"""
        js_content = self.js_editor.get(1.0, tk.END).strip()
        if js_content:
            self.root.clipboard_clear()
            self.root.clipboard_append(js_content)
            self.add_message("📋 JavaScript copied to clipboard", 'success')
        else:
            messagebox.showinfo("Info", "No JavaScript code to copy!")

    # View operations
    def toggle_theme(self):
        """Toggle between light and dark themes"""
        current = self.current_theme.get()
        self.current_theme.set("light" if current == "dark" else "dark")
        self.apply_theme()
        
        theme_name = "Light" if self.current_theme.get() == "light" else "Dark"
        self.add_message(f"🎨 Switched to {theme_name} theme", 'info')

    def zoom_in(self):
        """Increase font size"""
        current_size = self.font_size.get()
        if current_size < 24:
            self.font_size.set(current_size + 1)
            self.update_font_size()

    def zoom_out(self):
        """Decrease font size"""
        current_size = self.font_size.get()
        if current_size > 8:
            self.font_size.set(current_size - 1)
            self.update_font_size()

    def reset_zoom(self):
        """Reset font size to default"""
        self.font_size.set(12)
        self.update_font_size()

    def update_font_size(self):
        """Update font size for all text widgets"""
        size = self.font_size.get()
        
        if hasattr(self, 'python_editor'):
            self.python_editor.configure(font=('Consolas', size))
            self.js_editor.configure(font=('Consolas', size))
            self.line_numbers.configure(font=('Consolas', size))
            self.messages_text.configure(font=('Consolas', max(8, size - 2)))

    # Sample loading
    def load_sample(self, sample_name):
        """Load sample code"""
        samples = {
            "welcome": """# 🎉 Welcome to Python → JavaScript Transpiler!

def greet(name):
    return "Hello, " + name + "!"

message = greet("World")
print(message)""",
            
            "factorial": """def factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

# Test factorial function
for i in range(6):
    result = factorial(i)
    print("factorial(" + str(i) + ") = " + str(result))""",
            
            "fibonacci": """def fibonacci(n):
    if n <= 0:
        return 0
    elif n == 1:
        return 1
    else:
        a = 0
        b = 1
        for i in range(2, n + 1):
            temp = a + b
            a = b
            b = temp
        return b

# Generate Fibonacci sequence
print("Fibonacci sequence:")
for i in range(10):
    fib = fibonacci(i)
    print("F(" + str(i) + ") = " + str(fib))""",
            
            "lists": """# List operations example
numbers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

# Calculate sum
total = 0
for num in numbers:
    total += num

print("Numbers:", numbers)
print("Sum:", total)
print("Length:", len(numbers))

# Find even numbers
evens = []
for num in numbers:
    if num % 2 == 0:
        evens.append(num)

print("Even numbers:", evens)""",
            
            "control": """# Control flow examples

def check_number(x):
    if x > 0:
        return "positive"
    elif x < 0:
        return "negative"
    else:
        return "zero"

# Test different numbers
test_numbers = [-5, 0, 3, -1, 10]

for num in test_numbers:
    result = check_number(num)
    print(str(num) + " is " + result)

# Countdown loop
print("Countdown:")
count = 5
while count > 0:
    print(count)
    count -= 1
print("Done!")""",
            
            "functions": """def calculate_area(shape, width=0, height=0, radius=0):
    if shape == "rectangle":
        return width * height
    elif shape == "circle":
        return 3.14159 * radius * radius
    elif shape == "triangle":
        return 0.5 * width * height

def create_report(name, age=25, city="Unknown"):
    return "Name: " + name + ", Age: " + str(age) + ", City: " + city

# Test functions
rect_area = calculate_area("rectangle", 5, 3)
circle_area = calculate_area("circle", 0, 0, 4)

print("Rectangle area:", rect_area)
print("Circle area:", circle_area)

report1 = create_report("Alice", 30, "New York")
report2 = create_report("Bob")

print(report1)
print(report2)"""
        }
        
        if sample_name in samples:
            if self.is_modified:
                result = messagebox.askyesno(
                    "Load Sample", 
                    "Loading a sample will replace your current code. Continue?"
                )
                if not result:
                    return
            
            self.python_editor.delete(1.0, tk.END)
            self.python_editor.insert(1.0, samples[sample_name])
            self.is_modified = False
            self.current_python_file = None
            
            self.update_status()
            self.update_line_numbers()
            self.update_statistics()
            
            # Auto-transpile
            if self.auto_transpile_enabled.get():
                self.schedule_auto_transpile()
            
            sample_titles = {
                "welcome": "Welcome Example",
                "factorial": "Factorial Function",
                "fibonacci": "Fibonacci Sequence", 
                "lists": "List Operations",
                "control": "Control Flow",
                "functions": "Advanced Functions"
            }
            
            title = sample_titles.get(sample_name, sample_name.title())
            self.add_message(f"📚 Loaded sample: {title}", 'info')

    # Utility methods
    def add_to_recent_files(self, filename):
        """Add file to recent files list"""
        if filename in self.recent_files:
            self.recent_files.remove(filename)
        
        self.recent_files.insert(0, filename)
        
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
        
        self.update_recent_menu()

    def update_recent_menu(self):
        """Update recent files menu"""
        self.recent_menu.delete(0, tk.END)
        
        if not self.recent_files:
            self.recent_menu.add_command(label="(No recent files)", state='disabled')
        else:
            for i, filename in enumerate(self.recent_files):
                display_name = os.path.basename(filename)
                self.recent_menu.add_command(
                    label=f"{i+1}. {display_name}",
                    command=lambda f=filename: self.open_recent_file(f)
                )

    def open_recent_file(self, filename):
        """Open a recent file"""
        if os.path.exists(filename):
            # Save current file if modified
            if self.is_modified:
                result = messagebox.askyesnocancel(
                    "Unsaved Changes",
                    "Save changes before opening recent file?"
                )
                if result is None:
                    return
                elif result:
                    if not self.save_file():
                        return
            
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                self.python_editor.delete(1.0, tk.END)
                self.python_editor.insert(1.0, content)
                
                self.current_python_file = filename
                self.is_modified = False
                self.update_status()
                self.update_line_numbers()
                self.update_statistics()
                
                if self.auto_transpile_enabled.get():
                    self.schedule_auto_transpile()
                
                basename = os.path.basename(filename)
                self.add_message(f"📂 Opened recent: {basename}", 'success')
                
            except Exception as e:
                messagebox.showerror("Error", f"Could not open recent file:\n{e}")
                
        else:
            messagebox.showerror("Error", f"File not found:\n{filename}")
            self.recent_files.remove(filename)
            self.update_recent_menu()

    def load_settings(self):
        """Load application settings"""
        settings_file = os.path.join(os.path.expanduser("~"), ".transpiler_gui_settings.json")
        try:
            if os.path.exists(settings_file):
                with open(settings_file, 'r') as f:
                    settings = json.load(f)
                
                self.recent_files = settings.get('recent_files', [])
                self.font_size.set(settings.get('font_size', 12))
                self.current_theme.set(settings.get('theme', 'dark'))
                self.auto_transpile_enabled.set(settings.get('auto_transpile', True))
                
                # Apply loaded settings
                self.update_font_size()
                self.apply_theme()
                self.update_recent_menu()
                
                # Restore window geometry if available
                geometry = settings.get('window_geometry')
                if geometry:
                    try:
                        self.root.geometry(geometry)
                    except:
                        pass  # Invalid geometry string
                
        except Exception as e:
            print(f"Could not load settings: {e}")

    def save_settings(self):
        """Save application settings"""
        settings_file = os.path.join(os.path.expanduser("~"), ".transpiler_gui_settings.json")
        try:
            settings = {
                'recent_files': self.recent_files,
                'font_size': self.font_size.get(),
                'theme': self.current_theme.get(),
                'auto_transpile': self.auto_transpile_enabled.get(),
                'window_geometry': self.root.geometry()
            }
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
                
        except Exception as e:
            print(f"Could not save settings: {e}")

    # Dialog methods
    def show_language_guide(self):
        """Show language reference guide"""
        guide_text = """🐍 Python Features Supported:

🔧 FUNCTIONS:
• def function_name(parameters):
• return statements
• Local and global variables
• Default parameter values

🔀 CONTROL FLOW:
• if / elif / else statements
• while loops
• for loops with range() and lists
• break and continue statements

📊 DATA TYPES:
• Numbers (integers, floats)
• Strings with escape sequences
• Booleans (True, False)
• None value
• Lists [1, 2, 3] with indexing

⚡ OPERATORS:
• Arithmetic: +, -, *, /, //, %, **
• Comparison: ==, !=, <, >, <=, >=
• Logical: and, or, not
• Assignment: =, +=, -=

🛠️ BUILT-IN FUNCTIONS:
• print() → console.log()
• len() → .length property
• range() → helper function
• int(), float(), str() → type conversions

❌ LIMITATIONS:
• No dictionaries yet
• No classes or inheritance
• No imports or modules
• No exception handling (try/except)
• No list comprehensions

💡 TIP: Use the Samples menu to explore supported features!"""
        
        # Create custom dialog
        guide_window = tk.Toplevel(self.root)
        guide_window.title("Language Reference Guide")
        guide_window.geometry("600x700")
        guide_window.transient(self.root)
        guide_window.grab_set()
        
        # Configure colors
        colors = self.colors[self.current_theme.get()]
        guide_window.configure(bg=colors['bg'])
        
        # Create scrolled text widget
        text_frame = ttk.Frame(guide_window, style='Modern.TFrame', padding=20)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=('Consolas', 11),
            background=colors['editor_bg'],
            foreground=colors['editor_fg'],
            padx=15,
            pady=15
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(1.0, guide_text)
        text_widget.config(state=tk.DISABLED)
        
        # Close button
        button_frame = ttk.Frame(guide_window, style='Modern.TFrame', padding=10)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        ttk.Button(button_frame, text="Close", command=guide_window.destroy,
                  style='Modern.TButton').pack(side=tk.RIGHT)

    def show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_text = """⌨️ Keyboard Shortcuts:

📁 FILE OPERATIONS:
Ctrl+N          New file
Ctrl+O          Open file
Ctrl+S          Save file
Ctrl+Shift+S    Save as

✏️ EDIT OPERATIONS:
Ctrl+Z          Undo
Ctrl+Y          Redo
Ctrl+X          Cut
Ctrl+C          Copy
Ctrl+V          Paste
Ctrl+A          Select all

🔍 SEARCH:
Ctrl+F          Find text

👁️ VIEW:
Ctrl++          Zoom in
Ctrl+-          Zoom out
Ctrl+0          Reset zoom

🛠️ TOOLS:
F5              Transpile now

🚪 APPLICATION:
Ctrl+Q          Exit application

💡 TIP: Most operations are also available through the menu bar and toolbar!"""
        
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_text)

    def show_about(self):
        """Show about dialog"""
        about_text = """🐍➡️⚡ Python to JavaScript Transpiler
Version 2.0.0

A modern, feature-rich transpiler that converts 
Python-like syntax to JavaScript with real-time 
feedback and professional tools.

✨ FEATURES:
• Real-time auto-transpilation
• Syntax highlighting for both languages  
• Dark and light themes
• Complete file management
• Sample code library
• Find and replace functionality
• Zoom controls and customization
• Persistent settings

🛠️ BUILT WITH:
• Python 3.8+
• tkinter GUI framework
• Custom lexer and parser
• Visitor pattern code generation

📜 LICENSE:
MIT License - Free and open source

👨‍💻 DEVELOPED BY:
Aadrit Das
© 2024 All rights reserved

💡 TIP: Check the Samples menu to explore 
all supported Python features!"""
        
        messagebox.showinfo("About Transpiler", about_text)

    def exit_application(self):
        """Exit the application with confirmation"""
        if self.is_modified:
            result = messagebox.askyesnocancel(
                "Exit Application",
                "You have unsaved changes. Save before exiting?"
            )
            if result is None:  # Cancel
                return
            elif result:  # Yes, save first
                if not self.save_file():
                    return
        
        # Save settings before exit
        self.save_settings()
        
        # Clean shutdown
        self.root.quit()
        self.root.destroy()


def main():
    """Main application entry point"""
    # Create and configure root window
    root = tk.Tk()
    
    # Set window icon (if available)
    try:
        # This will work if you have an icon file
        root.iconbitmap('transpiler_icon.ico')
    except:
        pass  # No icon file available
    
    # Create application instance
    app = ModernTranspilerGUI(root)
    
    # Handle window close event
    root.protocol("WM_DELETE_WINDOW", app.exit_application)
    
    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")
    
    # Start the application
    root.mainloop()


if __name__ == "__main__":
    main()