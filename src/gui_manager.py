"""
Gestionnaire d'interface graphique pour NiTriTe V5.0
VERSION COMPLÈTE - Affiche TOUS les programmes disponibles (80+)
MODE SOMBRE Ordi Plus
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import json
from pathlib import Path
from datetime import datetime
import logging
import webbrowser
import subprocess
import win32com.client
import winshell
from PIL import Image, ImageTk

class NiTriteGUIComplet:
    """Interface graphique complète affichant TOUS les programmes"""
    
    # Couleurs du thème Ordi Plus (plus foncé que le site)
    DARK_BG = '#1a1a1a'          # Fond principal - Gris très foncé
    DARK_BG2 = '#2a2a2a'         # Fond secondaire - Gris foncé
    DARK_BG3 = '#333333'         # Fond tertiaire - Gris moyen foncé
    DARK_FG = '#ffffff'          # Texte principal - Blanc pur
    DARK_FG2 = '#cccccc'         # Texte secondaire - Gris clair
    ACCENT_ORANGE = '#FF6B00'    # Orange Ordi Plus (couleur principale)
    ACCENT_BLUE = '#003366'      # Bleu foncé Ordi Plus
    ACCENT_GREEN = '#00CC66'     # Vert succès
    ACCENT_RED = '#ff3333'       # Rouge erreur
    ACCENT_YELLOW = '#FFB800'    # Jaune warning (variante orange)
    PROGRESS_GREEN = '#2ecc71'   # Vert barre de progression
    BORDER = '#444444'           # Bordures
    
    def __init__(self, root, installer_manager=None, config_manager=None):
        self.root = root
        self.installer_manager = installer_manager
        self.config_manager = config_manager
        self.logger = logging.getLogger(__name__)
        
        # Variables pour les programmes
        self.program_vars = {}
        self.programs = {}
        self.category_frames = {}
        self.category_widgets = {}
        self.collapsed_categories = set()
        self.is_installing = False
        self.installation_start_time = None  # Pour calculer le temps restant
        
        # Charger le logo Ordi Plus pour l'arrière-plan
        self.load_background_logo()
        
        # Charger TOUS les programmes
        self.load_all_programs()
        
        # Interface
        self.setup_window()
        self.setup_styles()
        self.create_main_interface()
        
        # Protocole de fermeture propre
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def load_background_logo(self):
        """Charge le logo Ordi Plus pour l'arrière-plan avec transparence"""
        try:
            import sys
            # Chemins compatibles PyInstaller
            if getattr(sys, 'frozen', False):
                # Mode exécutable
                base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
            else:
                # Mode développement
                base_path = Path(__file__).parent.parent

            logo_path = base_path / 'assets' / 'logo_ordiplus_bg.png'
            if logo_path.exists():
                # Charger le logo
                img = Image.open(logo_path)

                # Redimensionner à 400x400 pixels
                img = img.resize((400, 400), Image.Resampling.LANCZOS)

                # Appliquer 15% d'opacité (85% de transparence)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                # Réduire l'opacité à 15%
                alpha = img.split()[3]
                alpha = alpha.point(lambda p: int(p * 0.15))
                img.putalpha(alpha)

                self.bg_logo = ImageTk.PhotoImage(img)
            else:
                self.bg_logo = None
                self.logger.warning(f"Logo Ordi Plus non trouvé : {logo_path}")
        except Exception as e:
            self.bg_logo = None
            self.logger.error(f"Erreur chargement logo : {e}")
    
    def setup_window(self):
        """Configure la fenêtre principale en plein écran"""
        self.root.title("🚀 NiTriTe V5.0 - Installateur Automatique de Programmes (80+ applications)")
        
        # MAXIMISER complètement la fenêtre
        self.root.state('zoomed')
        
        # Configuration responsive
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        # Couleur de fond SOMBRE
        self.root.configure(bg=self.DARK_BG)
        
        # Icône (si disponible)
        try:
            import sys
            # Chemins compatibles PyInstaller
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
            else:
                base_path = Path(__file__).parent.parent
            
            icon_path = base_path / 'assets' / 'icon.ico'
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except Exception as e:
            self.logger.warning(f"Impossible de charger l'icône: {e}")
    
    def setup_styles(self):
        """Configure les styles pour mode sombre"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configuration globale MODE SOMBRE
        style.configure('.',
                       background=self.DARK_BG,
                       foreground=self.DARK_FG,
                       fieldbackground=self.DARK_BG2,
                       bordercolor=self.BORDER,
                       darkcolor=self.DARK_BG,
                       lightcolor=self.DARK_BG3)
        
        # Labels
        style.configure('TLabel',
                       background=self.DARK_BG,
                       foreground=self.DARK_FG)
        
        # Frames
        style.configure('TFrame',
                       background=self.DARK_BG)
        
        # LabelFrames
        style.configure('TLabelframe',
                       background=self.DARK_BG,
                       foreground=self.ACCENT_BLUE,
                       bordercolor=self.BORDER)
        style.configure('TLabelframe.Label',
                       background=self.DARK_BG,
                       foreground=self.ACCENT_BLUE,
                       font=('Segoe UI', 10, 'bold'))
        
        # Boutons
        style.configure('TButton',
                       background=self.DARK_BG2,
                       foreground=self.DARK_FG,
                       bordercolor=self.BORDER,
                       font=('Segoe UI', 8))
        style.map('TButton',
                 background=[('active', self.DARK_BG3), ('pressed', self.ACCENT_ORANGE)],  # Orange au clic
                 foreground=[('active', self.DARK_FG)])
        
        # Checkbuttons
        style.configure('TCheckbutton',
                       background=self.DARK_BG,
                       foreground=self.DARK_FG,
                       font=('Segoe UI', 9))
        style.map('TCheckbutton',
                 background=[('active', self.DARK_BG)])
        
        # Styles spécialisés
        style.configure('Title.TLabel', 
                       font=('Segoe UI', 16, 'bold'),
                       foreground=self.ACCENT_ORANGE,  # Orange Ordi Plus pour le titre
                       background=self.DARK_BG)
        
        style.configure('Category.TLabel', 
                       font=('Segoe UI', 11, 'bold'),
                       foreground=self.ACCENT_ORANGE,  # Orange Ordi Plus pour les catégories
                       background=self.DARK_BG)
        
        style.configure('Action.TButton',
                       font=('Segoe UI', 11, 'bold'),
                       padding=8,
                       background=self.ACCENT_ORANGE,  # Orange Ordi Plus pour les boutons d'action
                       foreground='#ffffff')
        style.map('Action.TButton',
                 background=[('active', '#ff8533'), ('pressed', '#cc5500')])  # Variations d'orange

        # Barre de progression verte
        style.configure('Green.Horizontal.TProgressbar',
                       background=self.PROGRESS_GREEN,
                       troughcolor=self.DARK_BG2,
                       bordercolor=self.BORDER,
                       darkcolor=self.PROGRESS_GREEN,
                       lightcolor=self.PROGRESS_GREEN,
                       thickness=20)

        style.configure('Select.TButton',
                       font=('Segoe UI', 9, 'bold'),
                       padding=4)
    
    def load_all_programs(self):
        """Charge TOUS les programmes depuis programs.json"""
        try:
            import sys
            # Chemins compatibles PyInstaller
            if getattr(sys, 'frozen', False):
                base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
            else:
                base_path = Path(__file__).parent.parent
            
            programs_file = base_path / 'data' / 'programs.json'
            
            if programs_file.exists():
                with open(programs_file, 'r', encoding='utf-8') as f:
                    self.programs = json.load(f)
                
                # Compter le total
                total = sum(len(progs) if isinstance(progs, dict) else 0 
                          for progs in self.programs.values())
                
                self.logger.info(f"✅ {total} programmes chargés depuis {len(self.programs)} catégories")
                
            else:
                self.logger.warning("⚠️ Fichier programs.json non trouvé")
                self.programs = {}
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors du chargement des programmes: {e}")
            self.programs = {}
    
    def create_main_interface(self):
        """Crée l'interface principale avec PanedWindow redimensionnable et logo en arrière-plan"""
        # Frame principal MODE SOMBRE
        main_frame = ttk.Frame(self.root, padding="5")
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)
        
        # Logo en arrière-plan (si disponible) - placé en premier pour être derrière
        if self.bg_logo:
            bg_label = tk.Label(main_frame, image=self.bg_logo, bg=self.DARK_BG)
            bg_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # En-tête
        self.create_header(main_frame)
        
        # Barre d'actions (AVANT pour initialiser selection_label)
        self.create_action_bar(main_frame)
        
        # PanedWindow pour séparer programmes et outils avec diviseur draggable
        self.paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        self.paned_window.grid(row=2, column=0, sticky="nsew")
        
        # Frame gauche pour les programmes
        programs_container = ttk.Frame(self.paned_window)
        self.paned_window.add(programs_container, weight=4)

        # Frame droit pour les outils (ratio 4:3 pour élargir le panneau d'outils)
        tools_container = ttk.Frame(self.paned_window)
        self.paned_window.add(tools_container, weight=3)
        
        # Zone principale des programmes (dans le container gauche)
        self.create_programs_area_in_container(programs_container)
        
        # Panel d'outils à droite (dans le container droit)
        self.create_tools_panel_in_container(tools_container)
    
    def create_header(self, parent):
        """Crée l'en-tête"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        
        # Calcul du nombre total de programmes
        total_programs = sum(len(progs) if isinstance(progs, dict) else 0 
                           for progs in self.programs.values())
        
        # Titre MODE SOMBRE
        title_label = ttk.Label(
            header_frame,
            text=f"🎯 NITRITE v.2 - {total_programs} APPLICATIONS",
            style='Title.TLabel'
        )
        title_label.pack()
        
        # Sous-titre MODE SOMBRE
        subtitle_label = ttk.Label(
            header_frame,
            text="Installation silencieuse • Sources officielles",
            font=('Segoe UI', 9),
            foreground=self.DARK_FG2,
            background=self.DARK_BG
        )
        subtitle_label.pack(pady=(2, 0))
    
    def create_programs_area_in_container(self, parent):
        """Crée la zone des programmes avec TOUS les programmes affichés"""
        programs_frame = ttk.LabelFrame(parent, text="📋 PROGRAMMES", padding=3)
        programs_frame.pack(fill="both", expand=True)
        programs_frame.grid_rowconfigure(0, weight=1)
        programs_frame.grid_columnconfigure(0, weight=1)
        
        # Canvas principal avec scrollbar MODE SOMBRE
        self.main_canvas = tk.Canvas(
            programs_frame,
            bg=self.DARK_BG,
            highlightthickness=0
        )

        # Ajouter le logo OrdiPlus en filigrane (centré, 400x400, 15% opacité)
        if self.bg_logo:
            # Le logo sera centré après le premier redimensionnement de la fenêtre
            self.watermark_id = self.main_canvas.create_image(
                0, 0,  # Position temporaire, sera centrée plus tard
                image=self.bg_logo,
                anchor="center"
            )
            # Centrer le logo lors du redimensionnement du canvas
            self.main_canvas.bind('<Configure>', self._center_watermark)

        main_scrollbar = ttk.Scrollbar(programs_frame, orient="vertical", command=self.main_canvas.yview)
        self.scrollable_frame = ttk.Frame(self.main_canvas)
        
        # Configuration du scroll
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
        )
        
        self.main_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=1800)
        self.main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        # Placement
        self.main_canvas.grid(row=0, column=0, sticky="nsew")
        main_scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Bind scroll avec molette
        self.main_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        
        # Créer les checkboxes pour TOUS les programmes
        self.create_all_program_checkboxes()
        
        # Mettre à jour le compteur initial
        if hasattr(self, 'selection_label'):
            self.update_selection_count()
    
    def safe_update_selection_count(self):
        """Version sûre de update_selection_count"""
        if hasattr(self, 'selection_label'):
            self.update_selection_count()
    
    def create_all_program_checkboxes(self):
        """Crée les checkboxes pour TOUS les programmes par catégorie"""
        row = 0
        
        # Icônes pour les catégories
        category_icons = {
            'Navigateurs': '🌐',
            'Développement': '💻',
            'Bureautique': '📝',
            'Multimédia': '🎨',
            'Utilitaires': '🔧',
            'Communication': '💬',
            'Jeux': '🎮',
            'Sécurité': '🛡️',
            'Internet': '🌍',
            'Outils OrdiPlus': '🛠️',
            'Pack Office': '📦'
        }
        
        # Ordre d'affichage des catégories (OrdiPlus en premier)
        category_order = [
            'Outils OrdiPlus',
            'Pack Office',
            'Navigateurs',
            'Bureautique',
            'Multimédia',
            'Développement',
            'Utilitaires',
            'Sécurité',
            'Communication',
            'Jeux',
            'Internet'
        ]
        
        # Afficher dans l'ordre défini
        sorted_categories = []
        for cat in category_order:
            if cat in self.programs and isinstance(self.programs[cat], dict) and len(self.programs[cat]) > 0:
                sorted_categories.append((cat, self.programs[cat]))
        
        # Ajouter les catégories manquantes
        for category, programs in sorted(self.programs.items()):
            if category not in category_order and isinstance(programs, dict) and len(programs) > 0:
                sorted_categories.append((category, programs))
        
        for category, programs in sorted_categories:
            icon = category_icons.get(category, '📦')
            
            # Titre de catégorie avec bouton plier/déplier MODE SOMBRE
            category_header = ttk.Frame(self.scrollable_frame)
            category_header.grid(row=row, column=0, sticky="ew", pady=(8, 3), padx=5)
            category_header.grid_columnconfigure(1, weight=1)
            
            # Bouton plier/déplier
            collapse_btn = ttk.Button(
                category_header,
                text="▼",
                width=3,
                command=lambda cat=category: self.toggle_category(cat)
            )
            collapse_btn.grid(row=0, column=0, padx=(0, 5))
            
            # Label de catégorie MODE SOMBRE
            category_label = ttk.Label(
                category_header,
                text=f"{icon} {category.upper()} - {len(programs)} programmes",
                style='Category.TLabel',
                font=('Segoe UI', 11, 'bold')
            )
            category_label.grid(row=0, column=1, sticky="w")
            
            # Bouton sélectionner tout dans cette catégorie
            select_cat_btn = ttk.Button(
                category_header,
                text="✓ Tout",
                width=8,
                command=lambda c=category: self.select_category(c)
            )
            select_cat_btn.grid(row=0, column=2, padx=(5, 0))
            
            row += 1
            
            # Ligne de séparation MODE SOMBRE
            separator = ttk.Separator(self.scrollable_frame, orient='horizontal')
            separator.grid(row=row, column=0, sticky="ew", pady=(0, 3))
            row += 1
            
            # Frame pour les programmes de cette catégorie MODE SOMBRE
            programs_container = ttk.Frame(self.scrollable_frame)
            programs_container.grid(row=row, column=0, sticky="ew", padx=15)
            
            # 5 COLONNES pour gagner de la place
            for i in range(5):
                programs_container.grid_columnconfigure(i, weight=1)
            
            # Stocker les widgets pour le plier/déplier
            self.category_widgets[category] = {
                'collapse_btn': collapse_btn,
                'programs_container': programs_container
            }
            
            # Programmes en 5 colonnes pour maximiser l'affichage
            prog_row = 0
            col = 0
            
            checkbox_count = 0
            button_count = 0
            
            for program_name, program_info in sorted(programs.items()):
                # Frame pour ce programme (COMPACT)
                prog_frame = ttk.Frame(programs_container)
                prog_frame.grid(row=prog_row, column=col, sticky="w", padx=3, pady=2)
                
                # Vérifier si c'est un désinstallateur (catégorie spéciale)
                is_uninstaller = category == "Désinstallateurs Antivirus"
                
                # Tous les programmes ont maintenant une checkbox
                checkbox_count += 1
                var = tk.BooleanVar()
                self.program_vars[program_name] = var
                
                # Checkbox avec nom du programme (POLICE PLUS PETITE)
                checkbox = ttk.Checkbutton(
                    prog_frame,
                    text=program_name,
                    variable=var,
                    style='Program.TCheckbutton'
                )
                checkbox.pack(anchor='w')
                
                # Configurer la police plus petite
                checkbox.configure(style='Program.TCheckbutton')
                
                # Lier manuellement le changement
                var.trace_add('write', lambda *args: self.safe_update_selection_count())
                
                # Pour les désinstallateurs, ajouter un bouton de téléchargement en plus
                if is_uninstaller:
                    download_url = program_info.get('download_url', '')
                    if download_url:
                        download_btn = ttk.Button(
                            prog_frame,
                            text="📥 Télécharger",
                            command=lambda url=download_url: self.open_download_link(url),
                            width=15
                        )
                        download_btn.pack(anchor='w', padx=(20, 0), pady=(2, 0))
                
                # Description (SI DISPONIBLE et COURTE)
                desc = program_info.get('description', '')
                if desc and len(desc) < 60:
                    desc_label = ttk.Label(
                        prog_frame,
                        text=desc[:40] + "..." if len(desc) > 40 else desc,
                        font=('Segoe UI', 7),
                        foreground='#7f8c8d'
                    )
                    desc_label.pack(anchor='w', padx=(20, 0))
                
                # Passer à la colonne suivante
                col += 1
                if col >= 5:  # 5 colonnes
                    col = 0
                    prog_row += 1
            
            # Logger le nombre de checkboxes créées pour cette catégorie
            if checkbox_count > 0 or button_count > 0:
                self.logger.info(f"📊 {category}: {checkbox_count} checkboxes, {button_count} boutons")
            
            row += 1
    
    def toggle_category(self, category):
        """Plie ou déplie une catégorie"""
        if category in self.category_widgets:
            widgets = self.category_widgets[category]
            
            if category in self.collapsed_categories:
                # Déplier
                widgets['programs_container'].grid()
                widgets['collapse_btn'].config(text="▼")
                self.collapsed_categories.remove(category)
            else:
                # Plier
                widgets['programs_container'].grid_remove()
                widgets['collapse_btn'].config(text="▶")
                self.collapsed_categories.add(category)
            
            # Mettre à jour la région de défilement
            self.scrollable_frame.update_idletasks()
            self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all"))
    
    def create_action_bar(self, parent):
        """Crée la barre d'actions"""
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=1, column=0, sticky="ew", pady=(5, 0))
        action_frame.grid_columnconfigure(1, weight=1)
        
        # Label de sélection (PLUS COMPACT)
        self.selection_label = ttk.Label(
            action_frame,
            text="0 programme(s) sélectionné(s)",
            font=('Segoe UI', 11, 'bold'),
            foreground='#2c3e50'
        )
        self.selection_label.grid(row=0, column=0, sticky="w", padx=5)

        # Frame pour la barre de progression et son label
        progress_container = ttk.Frame(action_frame)
        progress_container.grid(row=0, column=1, sticky="ew", padx=15)
        progress_container.grid_columnconfigure(0, weight=1)

        # Label pour le pourcentage et temps restant (au-dessus de la barre)
        self.progress_label = ttk.Label(
            progress_container,
            text="",
            font=('Segoe UI', 9),
            foreground=self.PROGRESS_GREEN
        )
        self.progress_label.grid(row=0, column=0, sticky="ew")

        # Barre de progression VERTE
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_container,
            variable=self.progress_var,
            maximum=100,
            length=200,
            style='Green.Horizontal.TProgressbar'
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew")
        
        # Bouton d'organisation des programmes
        self.organize_button = ttk.Button(
            action_frame,
            text="🔄 ORGANISER",
            command=self.open_organize_dialog,
            style='Action.TButton'
        )
        self.organize_button.grid(row=0, column=2, sticky="e", padx=5)
        
        # Bouton d'ajout de programme
        self.add_program_button = ttk.Button(
            action_frame,
            text="➕ AJOUTER",
            command=self.add_custom_program,
            style='Action.TButton'
        )
        self.add_program_button.grid(row=0, column=3, sticky="e", padx=5)
        
        # Bouton d'installation (PLUS COMPACT)
        self.install_button = ttk.Button(
            action_frame,
            text="🚀 INSTALLER",
            command=self.start_installation,
            style='Action.TButton',
            state='disabled'  # Initialement désactivé
        )
        self.install_button.grid(row=0, column=4, sticky="e", padx=5)
    
    def _on_mousewheel(self, event):
        """Gestion du scroll avec la molette"""
        self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _center_watermark(self, event=None):
        """Centre le logo en filigrane dans le canvas"""
        if hasattr(self, 'bg_logo') and self.bg_logo and hasattr(self, 'watermark_id'):
            # Obtenir la taille du canvas
            canvas_width = self.main_canvas.winfo_width()
            canvas_height = self.main_canvas.winfo_height()

            # Centrer le logo
            center_x = canvas_width // 2
            center_y = canvas_height // 2

            # Mettre à jour la position du logo
            self.main_canvas.coords(self.watermark_id, center_x, center_y)

            # S'assurer que le logo reste en arrière-plan
            self.main_canvas.tag_lower(self.watermark_id)

    def select_all_programs(self):
        """Sélectionne TOUS les programmes"""
        for var in self.program_vars.values():
            var.set(True)
        self.update_selection_count()
    
    def deselect_all_programs(self):
        """Désélectionne tous les programmes"""
        for var in self.program_vars.values():
            var.set(False)
        self.update_selection_count()
    
    def select_category(self, category):
        """Sélectionne tous les programmes d'une catégorie"""
        if category in self.programs:
            for program_name in self.programs[category]:
                if program_name in self.program_vars:
                    self.program_vars[program_name].set(True)
        self.update_selection_count()
    
    def update_selection_count(self):
        """Met à jour le compteur de sélection"""
        selected_count = sum(1 for var in self.program_vars.values() if var.get())
        total_count = len(self.program_vars)
        
        self.selection_label.config(
            text=f"{selected_count} programme(s) sélectionné(s) sur {total_count}"
        )
        
        # Activer/désactiver le bouton
        if selected_count > 0:
            self.install_button.config(state='normal')
        else:
            self.install_button.config(state='disabled')
    
    def start_installation(self):
        """Démarre l'installation ou l'exécution de commandes"""
        self.logger.info("🔔 Bouton INSTALLER cliqué !")
        
        selected_programs = [
            name for name, var in self.program_vars.items() if var.get()
        ]
        
        self.logger.info(f"📊 Programmes sélectionnés: {len(selected_programs)}")
        self.logger.info(f"📋 Liste: {selected_programs}")
        
        if not selected_programs:
            messagebox.showwarning("Aucune sélection", "Veuillez sélectionner au moins un programme ou commande.")
            return
        
        # Séparer les commandes des programmes
        commands_to_run = []
        programs_to_install = []
        
        self.logger.info(f"🔍 Recherche dans programs_db...")
        
        for prog_name in selected_programs:
            # Chercher le programme dans la base de données
            prog_info = None
            for category_progs in self.programs.values():
                if prog_name in category_progs:
                    prog_info = category_progs[prog_name]
                    break
            
            self.logger.info(f"🔍 {prog_name} -> prog_info={prog_info is not None}, is_command={prog_info.get('is_command', False) if prog_info else 'N/A'}")
            
            if prog_info and prog_info.get('is_command'):
                commands_to_run.append((prog_name, prog_info))
                self.logger.info(f"➡️ {prog_name} ajouté aux commandes")
            else:
                programs_to_install.append(prog_name)
                self.logger.info(f"➡️ {prog_name} ajouté aux programmes à installer")
        
        # Exécuter les commandes immédiatement
        if commands_to_run:
            self.logger.info(f"⚡ Exécution de {len(commands_to_run)} commande(s)")
            self.execute_commands(commands_to_run)
        
        # Installer les programmes si nécessaire
        if programs_to_install:
            self.logger.info(f"📦 {len(programs_to_install)} programme(s) à installer")
            # Confirmation
            if messagebox.askyesno(
                "Confirmation d'installation",
                f"Installer {len(programs_to_install)} programme(s) ?\n\n"
                "L'installation sera automatique et silencieuse."
            ):
                self.logger.info(f"✅ Installation confirmée pour {len(programs_to_install)} programmes")
                
                # Désactiver le bouton d'installation
                self.is_installing = True
                self.install_button.config(state='disabled', text="⏳ Installation...")

                # Initialiser le temps de démarrage pour le calcul du temps restant
                import time
                self.installation_start_time = time.time()

                # Lancer l'installation dans un thread séparé
                if self.installer_manager:
                    self.logger.info(f"🚀 Démarrage du thread d'installation...")
                    install_thread = threading.Thread(
                        target=self.installer_manager.install_programs,
                        args=(
                            programs_to_install,
                            self.update_progress,
                            self.on_installation_finished
                        ),
                        daemon=True
                    )
                    install_thread.start()
                else:
                    self.logger.error("❌ InstallerManager n'est pas disponible!")
                    messagebox.showerror(
                        "Erreur",
                        "Le gestionnaire d'installation n'est pas disponible!"
                    )
                    self.is_installing = False
                    self.install_button.config(state='normal', text="🚀 INSTALLER")
            else:
                self.logger.info("❌ Installation annulée par l'utilisateur")
        elif not commands_to_run:
            self.logger.warning("⚠️ Aucune action à effectuer")
            messagebox.showwarning("Aucune sélection", "Aucune action à effectuer.")
    
    def execute_commands(self, commands_list):
        """Exécute les commandes Windows sélectionnées"""
        import subprocess
        
        executed_count = 0
        failed_count = 0
        
        for prog_name, prog_info in commands_list:
            command = prog_info.get('command', '')
            admin_required = prog_info.get('admin_required', False)
            
            try:
                if admin_required:
                    # Exécuter en mode administrateur avec PowerShell
                    ps_command = f'Start-Process cmd.exe -ArgumentList "/c {command}" -Verb RunAs'
                    subprocess.Popen(
                        ["powershell.exe", "-Command", ps_command],
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                else:
                    # Exécuter normalement
                    subprocess.Popen(
                        command,
                        shell=True,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                
                self.logger.info(f"✅ Commande exécutée: {prog_name}")
                executed_count += 1
                
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'exécution de {prog_name}: {e}")
                failed_count += 1
        
        # Désélectionner les commandes exécutées
        for prog_name, _ in commands_list:
            if prog_name in self.program_vars:
                self.program_vars[prog_name].set(False)
        
        self.update_selection_count()
        
        # Message de résultat
        if executed_count > 0:
            message = f"✅ {executed_count} commande(s) exécutée(s)"
            if failed_count > 0:
                message += f"\n⚠️ {failed_count} échec(s)"
            
            messagebox.showinfo("Commandes exécutées", message)

    
    def update_progress(self, value, message=""):
        """Met à jour la barre de progression avec pourcentage et temps restant"""
        import time

        self.progress_var.set(value)
        if message:
            self.selection_label.config(text=f"⏳ {message}")

        # Calculer et afficher le pourcentage et temps restant
        if value > 0 and self.installation_start_time:
            elapsed_time = time.time() - self.installation_start_time

            # Estimer le temps restant basé sur le pourcentage actuel
            if value > 0:
                total_estimated_time = (elapsed_time / value) * 100
                remaining_time = total_estimated_time - elapsed_time

                # Convertir en minutes et secondes
                remaining_minutes = int(remaining_time // 60)
                remaining_seconds = int(remaining_time % 60)

                # Formater le texte
                progress_text = f"{int(value)}% • Temps restant: {remaining_minutes}min {remaining_seconds}s"
            else:
                progress_text = f"{int(value)}%"
        else:
            # Pas d'installation en cours, vider le label
            progress_text = ""

        self.progress_label.config(text=progress_text)
        self.root.update_idletasks()
    
    def log_installation_message(self, message, level="info"):
        """Affiche un message de log"""
        print(f"[{level.upper()}] {message}")
        self.logger.info(message)
    
    def on_installation_finished(self, success):
        """Appelé quand l'installation est terminée"""
        self.is_installing = False
        self.installation_start_time = None  # Réinitialiser le temps de démarrage
        self.install_button.config(state='normal', text="🚀 INSTALLER")

        if success:
            messagebox.showinfo(
                "Installation terminée",
                "✅ L'installation de tous les programmes sélectionnés est terminée !\n\n"
                "Vérifiez vos applications installées."
            )
            # Créer le dossier "Outils de nettoyage" si nécessaire
            self.create_cleanup_folder()
            # Désélectionner tous les programmes
            self.deselect_all_programs()
        else:
            messagebox.showwarning(
                "Installation interrompue",
                "⚠️ L'installation a été interrompue.\n\n"
                "Certains programmes peuvent avoir été installés."
            )
        
        self.update_progress(0, "")
        self.update_selection_count()
    
    def create_cleanup_folder(self):
        """Crée le dossier 'Outils de nettoyage' sur le bureau avec les raccourcis"""
        try:
            import os
            import winshell
            from win32com.client import Dispatch
            
            desktop = winshell.desktop()
            cleanup_folder = Path(desktop) / "Outils de nettoyage"
            cleanup_folder.mkdir(exist_ok=True)
            
            # Programmes à inclure dans le dossier
            cleanup_programs = {
                "Malwarebytes": r"C:\Program Files\Malwarebytes\Anti-Malware\mbam.exe",
                "AdwCleaner": r"C:\Program Files\Malwarebytes\AdwCleaner\adwcleaner.exe",
                "Wise Disk Cleaner": r"C:\Program Files (x86)\Wise\Wise Disk Cleaner\WiseDiskCleaner.exe",
                "Spybot": r"C:\Program Files (x86)\Spybot - Search & Destroy 2\SDWelcome.exe"
            }
            
            # Télécharger les portables
            portable_downloads = Path(__file__).parent.parent / "downloads"
            anydesk_exe = portable_downloads / "AnyDesk.exe"
            rustdesk_exe = portable_downloads / "rustdesk.exe"
            
            # Copier les exécutables portables
            if anydesk_exe.exists():
                import shutil
                shutil.copy(anydesk_exe, cleanup_folder / "AnyDesk.exe")
            
            if rustdesk_exe.exists():
                import shutil
                shutil.copy(rustdesk_exe, cleanup_folder / "RustDesk.exe")
            
            # Créer les raccourcis
            shell = Dispatch('WScript.Shell')
            
            for prog_name, exe_path in cleanup_programs.items():
                if Path(exe_path).exists():
                    shortcut_path = cleanup_folder / f"{prog_name}.lnk"
                    shortcut = shell.CreateShortCut(str(shortcut_path))
                    shortcut.Targetpath = exe_path
                    shortcut.WorkingDirectory = str(Path(exe_path).parent)
                    shortcut.IconLocation = exe_path
                    shortcut.save()
            
            self.logger.info(f"✅ Dossier 'Outils de nettoyage' créé sur le bureau")
            
        except Exception as e:
            self.logger.warning(f"⚠️ Impossible de créer le dossier Outils de nettoyage: {e}")
    
    def open_massgrave(self):
        """Ouvre le site MAS dans le navigateur"""
        import webbrowser
        webbrowser.open("https://massgrave.dev/")
        self.logger.info("🔐 Ouverture du site MAS (Microsoft Activation Scripts)")
    
    def activate_windows(self):
        """Lance la commande d'activation Windows en admin"""
        if messagebox.askyesno(
            "Activation Windows",
            "⚡ Cette commande va lancer le script d'activation Windows.\n\n"
            "Voulez-vous continuer ?\n\n"
            "Note: Un terminal PowerShell s'ouvrira avec les privilèges administrateur."
        ):
            try:
                import subprocess
                
                # Commande PowerShell à exécuter en admin
                command = 'irm https://get.activated.win | iex'
                
                # Lancer PowerShell en admin avec fenêtre visible - MÉTHODE CORRIGÉE
                ps_command = f'Start-Process powershell.exe -Verb RunAs -ArgumentList "-NoExit","-Command","irm https://get.activated.win | iex"'
                
                subprocess.Popen(
                    ['powershell.exe', '-Command', ps_command],
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0
                )
                
                self.logger.info("⚡ Commande d'activation Windows lancée")
                messagebox.showinfo(
                    "Activation lancée",
                    "✅ Le script d'activation a été lancé !\n\n"
                    "Suivez les instructions dans la fenêtre PowerShell."
                )
                
            except Exception as e:
                self.logger.error(f"❌ Erreur lors de l'activation: {e}")
                messagebox.showerror(
                    "Erreur",
                    f"❌ Impossible de lancer l'activation:\n{e}"
                )
    
    def create_tools_panel_in_container(self, parent):
        """Crée le panel d'outils à droite avec sections REDIMENSIONNABLES et RÉORGANISABLES"""
        tools_frame = ttk.LabelFrame(parent, text="🛠️ OUTILS WINDOWS - Glissez les titres pour réorganiser", padding=5)
        tools_frame.pack(fill="both", expand=True)
        
        # PanedWindow VERTICAL pour les sections redimensionnables
        self.tools_paned = ttk.PanedWindow(tools_frame, orient=tk.VERTICAL)
        self.tools_paned.pack(fill="both", expand=True)
        
        # Initialiser l'ordre des sections (peut être modifié par drag & drop)
        self.sections_order = ['reparation', 'activation', 'maintenance', 'diagnostics', 'reseau', 'winget', 'parametres', 'support', 'fournisseurs', 'securite', 'benchmark', 'depannage', 'drivers', 'documentation']
        self.section_widgets = {}

        # Créer toutes les sections
        self.create_reparation_section()
        self.create_activation_section()
        self.create_maintenance_section()
        self.create_diagnostics_section()
        self.create_reseau_section()
        self.create_winget_section()
        self.create_parametres_section()
        self.create_support_section()
        self.create_fournisseurs_section()
        self.create_securite_section()
        self.create_benchmark_section()
        self.create_depannage_section()
        self.create_drivers_section()
        self.create_documentation_section()

        # Ajouter les sections dans l'ordre initial
        for section_name in self.sections_order:
            if section_name in self.section_widgets:
                self.tools_paned.add(self.section_widgets[section_name])
    
    def create_reparation_section(self):
        """Crée la section Réparation Système - OPTIMISÉE"""
        section_frame = ttk.Frame(self.tools_paned)
        
        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🔧 RÉPARATION SYSTÈME", 'reparation')
        header.pack(fill="x", padx=2, pady=2)
        
        # Contenu avec hauteur fixe optimale (28 boutons en 4 colonnes = 7 lignes)
        content_frame = ttk.Frame(section_frame, height=180)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)  # Empêche l'expansion automatique
        
        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Boutons de réparation - EN 2 COLONNES
        dism_buttons = [
            ("🔍 DISM Vérifier", "DISM /Online /Cleanup-Image /CheckHealth"),
            ("🔎 DISM Scanner", "DISM /Online /Cleanup-Image /ScanHealth"),
            ("🔧 DISM Réparer", "DISM /Online /Cleanup-Image /RestoreHealth"),
            ("🧹 DISM Nettoyer", "DISM /Online /Cleanup-Image /StartComponentCleanup"),
            ("🧹+ DISM Nettoyer++", "DISM /Online /Cleanup-Image /StartComponentCleanup /ResetBase"),
            ("🛡️ SFC Scan", "sfc /scannow"),
            ("💿 ChkDsk C:", "chkdsk C: /F /R"),
            ("💾 ChkDsk Scan", "chkdsk C: /scan"),
            ("🔄 Réparer Boot", "bootrec /fixmbr & bootrec /fixboot & bootrec /rebuildbcd"),
            ("🧼 Nettoyer Store", "wsreset.exe"),
            ("🔥 Vider DNS", "ipconfig /flushdns"),
            ("🌐 Reset Winsock", "netsh winsock reset"),
            ("📡 Reset IP", "netsh int ip reset"),
            ("🔨 DISM+SFC Complet", "DISM /Online /Cleanup-Image /RestoreHealth & sfc /scannow"),
            ("⚙️ MSConfig", "msconfig"),
            ("ℹ️ WinVer", "winver"),
            ("🖥️ Propriétés Système", "sysdm.cpl"),
            ("📁 AppData", "explorer %appdata%"),
            ("🗑️ Temp", "explorer %temp%"),
            ("🌐 Programmes", "explorer shell:Programs"),
            ("🚀 Démarrage", "explorer shell:Startup"),
            ("💻 Système32", "explorer C:\\Windows\\System32"),
            ("🎛️ Gestionnaire périph.", "devmgmt.msc"),
            ("💾 Gestion disques", "diskmgmt.msc"),
            ("🔌 Services", "services.msc"),
            ("📋 Registre", "regedit"),
            ("🖨️ Imprimantes", "control printers")
        ]
        
        # Configuration 6 colonnes pour maximiser l'espace horizontal
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        for idx, (label, cmd) in enumerate(dism_buttons):
            row = idx // 6  # Division par 6 pour 6 colonnes
            col = idx % 6   # Modulo 6 pour alterner entre colonnes 0-5
            ttk.Button(
                scrollable,
                text=label,
                command=lambda c=cmd: self.execute_quick_command(c, True)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
        
        self.section_widgets['reparation'] = section_frame
    
    def create_activation_section(self):
        """Crée la section Activation & Téléchargements - 2 LIGNES"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🔑 ACTIVATION & TÉLÉCHARGEMENTS", 'activation')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu - DEUX LIGNES
        content_frame = ttk.Frame(section_frame)
        content_frame.pack(fill="x", padx=2, pady=3)

        # Grid 2 lignes x 5 colonnes
        button_container = ttk.Frame(content_frame)
        button_container.pack(fill="x")

        # Configuration de 5 colonnes avec weight égal
        for i in range(5):
            button_container.grid_columnconfigure(i, weight=1)

        # LIGNE 1 - Boutons originaux
        ttk.Button(button_container, text="🔐 MAS", command=self.open_massgrave).grid(row=0, column=0, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="⚡ Win", command=self.activate_windows).grid(row=0, column=1, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="📦 Office FR", command=lambda: self.open_manufacturer_support("https://gravesoft.dev/office_c2r_links#french-fr-fr")).grid(row=0, column=2, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="🌊 YGG", command=lambda: self.open_manufacturer_support("https://www.yggtorrent.top/auth/login")).grid(row=0, column=3, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="💾 BDD Portables", command=self.show_portable_database_stats).grid(row=0, column=4, padx=1, pady=2, sticky="ew")

        # LIGNE 2 - Nouveaux boutons obligatoires
        ttk.Button(button_container, text="📚 Archive.org", command=lambda: webbrowser.open("https://archive.org/")).grid(row=1, column=0, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="🎮 FitGirl Repacks", command=lambda: webbrowser.open("https://fitgirl-repacks.site/")).grid(row=1, column=1, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="🔧 MajorGeeks", command=lambda: webbrowser.open("https://www.majorgeeks.com/")).grid(row=1, column=2, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="🍎 EveryMac", command=lambda: webbrowser.open("https://everymac.com/")).grid(row=1, column=3, padx=1, pady=2, sticky="ew")
        ttk.Button(button_container, text="📦 Portable AppZ", command=lambda: webbrowser.open("https://portableappz.blogspot.com/")).grid(row=1, column=4, padx=1, pady=2, sticky="ew")

        self.section_widgets['activation'] = section_frame

    def create_maintenance_section(self):
        """Crée la section Maintenance & Nettoyage"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🧹 MAINTENANCE & NETTOYAGE", 'maintenance')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale (16 boutons en 4 colonnes = 4 lignes)
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        maintenance_buttons = [
            ("🗑️ Vider Corbeille", "PowerShell -Command \"Clear-RecycleBin -Force\""),
            ("🧹 Nettoyer Temp", "cleanmgr /sageset:1 & cleanmgr /sagerun:1"),
            ("📦 Disk Cleanup", "cleanmgr"),
            ("🗂️ Nettoyer WinSxS", "DISM /Online /Cleanup-Image /StartComponentCleanup"),
            ("🔄 Défragmenter C:", "defrag C: /O"),
            ("📊 Analyser Défrag", "dfrgui"),
            ("⚡ Gestionnaire Tâches", "taskmgr"),
            ("📈 Moniteur Ressources", "resmon"),
            ("💾 Nettoyage Disque", "cleanmgr /sagerun:1"),
            ("🗃️ Analyse Espace", "explorer C:\\"),
            ("🧹 Nettoyer Préfetch", "del /q /f C:\\Windows\\Prefetch\\*"),
            ("🗑️ Vider %TEMP%", "del /q /f %temp%\\* & rd /s /q %temp%"),
            ("📥 Nettoyer Downloads", "explorer %USERPROFILE%\\Downloads"),
            ("🗂️ Gestionnaire Stockage", "start ms-settings:storagesense"),
            ("🧼 Optimiser Disques", "dfrgui"),
            ("🔌 Désinstaller Apps", "appwiz.cpl")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        for idx, (label, cmd) in enumerate(maintenance_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda c=cmd: self.execute_quick_command(c, True)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['maintenance'] = section_frame

    def create_diagnostics_section(self):
        """Crée la section Diagnostics & Infos Système"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🔍 DIAGNOSTICS & INFOS", 'diagnostics')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale (16 boutons en 4 colonnes = 4 lignes)
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Boutons commandes Windows
        diagnostics_buttons = [
            ("💻 Infos Système", "msinfo32"),
            ("🎮 DirectX Diagnostic", "dxdiag"),
            ("📊 Observateur Événements", "eventvwr.msc"),
            ("📈 Moniteur Performances", "perfmon"),
            ("💾 Gestion Disques", "diskmgmt.msc"),
            ("🔧 Analyseur Fiabilité", "perfmon /rel"),
            ("🖥️ Propriétés Système", "sysdm.cpl"),
            ("ℹ️ Version Windows", "winver"),
            ("🔌 Gestionnaire Périph.", "devmgmt.msc"),
            ("🔋 Rapport Batterie", "powercfg /batteryreport"),
            ("⚡ Rapport Énergie", "powercfg /energy"),
            ("📡 Config Réseau", "ncpa.cpl"),
            ("🌡️ Temp Processeur", "wmic cpu get temperature"),
            ("💻 Config Matérielle", "msinfo32 /categories +ComponentsSummary"),
            ("🔍 Rapport Intégrité", "DISM /Online /Cleanup-Image /CheckHealth"),
            ("🧪 Test Mémoire", "MdSched.exe")
        ]

        # Boutons sites web diagnostics
        diagnostics_web_buttons = [
            ("🔍 Speccy", "https://www.ccleaner.com/speccy"),
            ("⚡ CPU-Z", "https://www.cpuid.com/softwares/cpu-z.html"),
            ("🎮 GPU-Z", "https://www.techpowerup.com/gpuz/"),
            ("💾 HWiNFO", "https://www.hwinfo.com/download/"),
            ("💿 CrystalDiskInfo", "https://crystalmark.info/en/software/crystaldiskinfo/"),
            ("📊 CrystalDiskMark", "https://crystalmark.info/en/software/crystaldiskmark/"),
            ("🛠️ Sysinternals Suite", "https://learn.microsoft.com/en-us/sysinternals/downloads/sysinternals-suite"),
            ("⚡ UserBenchmark", "https://www.userbenchmark.com/"),
            ("📈 AIDA64", "https://www.aida64.com/downloads"),
            ("🔧 HWMonitor", "https://www.cpuid.com/softwares/hwmonitor.html"),
            ("💻 PC-Wizard", "https://www.cpuid.com/softwares/pc-wizard.html"),
            ("🌡️ Core Temp", "https://www.alcpu.com/CoreTemp/"),
            ("📊 Open Hardware Monitor", "https://openhardwaremonitor.org/downloads/"),
            ("🔍 OCCT", "https://www.ocbase.com/"),
            ("⚙️ MSI Afterburner", "https://www.msi.com/Landing/afterburner/graphics-cards"),
            ("💾 HD Tune", "https://www.hdtune.com/download.html"),
            ("📈 AS SSD Benchmark", "https://www.alex-is.de/PHP/fusion/downloads.php?cat_id=4"),
            ("🛠️ Prime95", "https://www.mersenne.org/download/"),
            ("🔥 FurMark", "https://geeks3d.com/furmark/"),
            ("💻 Belarc Advisor", "https://www.belarc.com/products/belarc-advisor"),
            ("🔍 SIW", "https://www.gtopala.com/"),
            ("📊 CPUID HWMonitor Pro", "https://www.cpuid.com/softwares/hwmonitor-pro.html"),
            ("🌡️ SpeedFan", "http://www.almico.com/speedfan.php"),
            ("💾 Victoria", "https://hdd.by/victoria/"),
            ("🔧 MemTest86", "https://www.memtest86.com/download.htm"),
            ("📈 3DMark", "https://benchmarks.ul.com/3dmark"),
            ("💻 PCMark", "https://benchmarks.ul.com/pcmark10"),
            ("🔍 Geekbench", "https://www.geekbench.com/download/"),
            ("⚡ Cinebench", "https://www.maxon.net/en/cinebench"),
            ("🛠️ Intel Processor Diagnostic", "https://www.intel.com/content/www/us/en/download/15951/intel-processor-diagnostic-tool.html")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer boutons commandes Windows
        idx = 0
        for label, cmd in diagnostics_buttons:
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda c=cmd: self.execute_quick_command(c, True)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
            idx += 1

        # Créer boutons sites web diagnostics
        for label, url in diagnostics_web_buttons:
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
            idx += 1

        self.section_widgets['diagnostics'] = section_frame

    def create_reseau_section(self):
        """Crée la section Réseau & Internet"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🌐 RÉSEAU & INTERNET", 'reseau')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale (16 boutons en 4 colonnes = 4 lignes)
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Boutons commandes Windows réseau
        reseau_buttons = [
            ("🌐 Ping Google", "ping 8.8.8.8 -n 10"),
            ("🔍 Test DNS", "nslookup google.com"),
            ("📡 Afficher IP", "ipconfig /all"),
            ("🗺️ Traceroute", "tracert google.com"),
            ("📊 Netstat", "netstat -ano"),
            ("🔥 Vider DNS", "ipconfig /flushdns"),
            ("🌐 Reset Winsock", "netsh winsock reset"),
            ("📡 Reset IP", "netsh int ip reset"),
            ("🔌 Renouveler IP", "ipconfig /release & ipconfig /renew"),
            ("🛡️ Pare-feu", "firewall.cpl"),
            ("🌐 Config Réseau", "ncpa.cpl"),
            ("📈 Moniteur Réseau", "resmon"),
            ("🔍 Test Latence", "ping 8.8.8.8 -t"),
            ("📡 WiFi Info", "netsh wlan show interfaces"),
            ("🔐 Proxy Settings", "start ms-settings:network-proxy")
        ]

        # Boutons sites web réseau & internet
        reseau_web_buttons = [
            ("⚡ Speedtest.net", "https://www.speedtest.net/"),
            ("🚀 Fast.com", "https://fast.com/"),
            ("📊 DownDetector", "https://downdetector.com/"),
            ("🌐 WhatIsMyIP", "https://www.whatismyip.com/"),
            ("🔍 DNS Checker", "https://dnschecker.org/"),
            ("🛠️ Network Tools", "https://mxtoolbox.com/NetworkTools.aspx"),
            ("📡 Wireshark", "https://www.wireshark.org/download.html"),
            ("📈 PingPlotter", "https://www.pingplotter.com/download"),
            ("🌍 IP Location", "https://www.iplocation.net/"),
            ("🔒 DNS Leak Test", "https://www.dnsleaktest.com/"),
            ("⚡ TestMy.net", "https://testmy.net/"),
            ("📊 Bandwidth Place", "https://www.bandwidthplace.com/"),
            ("🌐 IP Chicken", "https://www.ipchicken.com/"),
            ("🔍 MX Toolbox", "https://mxtoolbox.com/"),
            ("📡 Packet Loss Test", "https://packetlosstest.com/"),
            ("🌍 Trace Route Online", "https://www.traceroute-online.com/"),
            ("🔒 IP Leak", "https://ipleak.net/"),
            ("⚡ Comparitech Speed Test", "https://www.comparitech.com/internet-providers/speed-test/"),
            ("📊 SpeedOf.Me", "https://speedof.me/"),
            ("🌐 Geolocation IP", "https://www.geolocation.com/"),
            ("🔍 Censys", "https://search.censys.io/"),
            ("📡 Shodan", "https://www.shodan.io/"),
            ("🌍 IP2Location", "https://www.ip2location.com/"),
            ("🔒 BrowserLeaks", "https://browserleaks.com/"),
            ("⚡ M-Lab Speed Test", "https://speed.measurementlab.net/"),
            ("📊 SourceForge Speed Test", "https://sourceforge.net/speedtest/"),
            ("🌐 Google Fiber Speed Test", "https://fiber.google.com/speedtest/"),
            ("🔍 Hurricane Electric Tools", "https://bgp.he.net/"),
            ("📡 Router Lookup", "https://www.routercheck.com/"),
            ("🌍 IP Address Guide", "https://www.ipaddressguide.com/")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer boutons commandes Windows
        idx = 0
        for label, cmd in reseau_buttons:
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda c=cmd: self.execute_quick_command(c, True)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
            idx += 1

        # Créer boutons sites web réseau
        for label, url in reseau_web_buttons:
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
            idx += 1

        self.section_widgets['reseau'] = section_frame

    def create_winget_section(self):
        """Crée la section Winget - Mises à jour"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🔄 WINGET - MISES À JOUR", 'winget')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale (12 boutons en 4 colonnes = 3 lignes)
        content_frame = ttk.Frame(section_frame, height=100)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)
        
        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Boutons Winget - EN 4 COLONNES
        winget_buttons = [
            ("🔄 MAJ Tout", "winget upgrade --all"),
            ("📋 Liste MAJ", "winget upgrade"),
            ("🔍 Recherche", "winget search"),
            ("📦 Liste installés", "winget list"),
            ("⚙️ Winget Info", "winget --info"),
            ("🧹 Nettoyer cache", "winget source reset --force"),
            ("📥 MAJ Chrome", "winget upgrade Google.Chrome"),
            ("🦊 MAJ Firefox", "winget upgrade Mozilla.Firefox"),
            ("📝 MAJ VSCode", "winget upgrade Microsoft.VisualStudioCode"),
            ("💬 MAJ Discord", "winget upgrade Discord.Discord"),
            ("🎮 MAJ Steam", "winget upgrade Valve.Steam"),
            ("🎵 MAJ Spotify", "winget upgrade Spotify.Spotify")
        ]
        
        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        for idx, (label, cmd) in enumerate(winget_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda c=cmd: self.execute_quick_command(c, True)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
        
        self.section_widgets['winget'] = section_frame
    
    def create_parametres_section(self):
        """Crée la section Paramètres - OPTIMISÉE"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "⚙️ PARAMÈTRES WINDOWS", 'parametres')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale (13 boutons en 4 colonnes = 4 lignes)
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)
        
        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        params_buttons = [
            ("⚙️ Paramètres", "start ms-settings:"),
            ("🌐 Réseau", "start ms-settings:network"),
            ("📡 Bluetooth", "start ms-settings:bluetooth"),
            ("🖨️ Imprimantes", "start ms-settings:printers"),
            ("🔊 Son", "start ms-settings:sound"),
            ("⌨️ Clavier", "start ms-settings:keyboard"),
            ("🔑 Activation", "start ms-settings:activation"),
            ("🔄 Update", "start ms-settings:windowsupdate"),
            ("📱 Périphériques", "start ms-settings:connecteddevices"),
            ("🎛️ Panneau", "control"),
            ("📦 Programmes", "appwiz.cpl"),
            ("⚙️ Services", "services.msc"),
            ("📝 Registre", "regedit")
        ]
        
        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        for idx, (label, cmd) in enumerate(params_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda c=cmd: self.execute_quick_command(c, False)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
        
        self.section_widgets['parametres'] = section_frame
    
    def create_support_section(self):
        """Crée la section Support Fabricants - OPTIMISÉE"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🏢 SUPPORT & DRIVERS", 'support')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale (12 boutons en 4 colonnes = 3 lignes)
        content_frame = ttk.Frame(section_frame, height=100)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)
        
        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        support_buttons = [
            ("💻 Lenovo Vantage", "https://support.lenovo.com/fr/fr/solutions/ht505081"),
            ("🖨️ HP Support", "https://support.hp.com/fr-fr/help/hp-support-assistant"),
            ("💻 Dell SupportAssist", "https://www.dell.com/support/home/fr-fr/product-support/product/supportassist-for-home-pcs/download"),
            ("🎮 MSI Center", "https://fr.msi.com/Landing/MSI-Center"),
            ("⚡ ASUS Support", "https://www.asus.com/fr/support/download-center/"),
            ("🖥️ Acer Support", "https://www.acer.com/fr-fr/support"),
            ("💾 Intel DSA", "https://www.intel.fr/content/www/fr/fr/support/detect.html"),
            ("🎮 AMD Software", "https://www.amd.com/fr/support"),
            ("🖥️ NVIDIA GeForce", "https://www.nvidia.com/fr-fr/geforce/geforce-experience/"),
            ("📱 Samsung Magician", "https://www.samsung.com/fr/support/computing/samsung-magician/"),
            ("🔌 Logitech G HUB", "https://www.logitechg.com/fr-fr/innovation/g-hub.html"),
            ("🖱️ Razer Synapse", "https://www.razer.com/fr-fr/synapse-3")
        ]
        
        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        for idx, (label, url) in enumerate(support_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: self.open_manufacturer_support(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
        
        self.section_widgets['support'] = section_frame

    def create_fournisseurs_section(self):
        """Crée la section Fournisseurs & Achats - 32+ sites"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🛒 FOURNISSEURS & ACHATS", 'fournisseurs')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Tous les sites fournisseurs et achats
        fournisseurs_buttons = [
            ("🔧 1fo Trade", "https://www.1fotrade.com/"),
            ("💻 Acadia Info", "https://www.acadia-info.com/"),
            ("📦 Flexit Distribution", "https://shop.flexitdistribution.com/"),
            ("💰 1fo Discount", "https://www.1fodiscount.com/"),
            ("🛒 Amazon FR", "https://www.amazon.fr/"),
            ("🏪 Cdiscount", "https://www.cdiscount.com/"),
            ("🌐 eBay FR", "https://www.ebay.fr/"),
            ("📢 Leboncoin", "https://www.leboncoin.fr/"),
            ("🖥️ Visiodirect", "https://www.visiodirect.net/"),
            ("🍎 OKA Mac", "https://www.okamac.com/fr/"),
            ("💼 Inmac Wstore", "https://www.inmac-wstore.com/"),
            ("💡 Idealo", "https://www.idealo.fr/"),
            ("🔥 Dealabs", "https://www.dealabs.com/"),
            ("🏬 Rue du Commerce", "https://www.rueducommerce.fr/"),
            ("🎌 Rakuten", "https://fr.shopping.rakuten.com/"),
            ("📦 Noriak Distri", "https://www.noriak-distri.com/"),
            ("🎮 Cougar Gaming", "https://www.cougargaming.fr/"),
            ("📚 Fnac", "https://www.fnac.com/"),
            ("💻 Grosbill", "https://www.grosbill.com/"),
            ("💾 Crucial FR", "https://www.crucial.fr/"),
            ("🔝 TopAchat", "https://www.topachat.com/"),
            ("🍎 MacWay", "https://www.macway.com/"),
            ("🚗 La Centrale", "https://www.lacentrale.fr/"),
            ("🔌 Darty", "https://www.darty.com/"),
            ("🏪 Boulanger", "https://www.boulanger.com/"),
            ("🛒 E.Leclerc", "https://www.e.leclerc/"),
            ("🇨🇭 Digitec CH", "https://www.digitec.ch/fr"),
            ("🔍 Le Dénicheur", "https://ledenicheur.fr/"),
            ("💼 Dell FR", "https://www.dell.com/fr-fr"),
            ("🖨️ HP FR", "https://www.hp.com/fr-fr/shop/"),
            ("💻 Lenovo FR", "https://www.lenovo.com/fr/fr/"),
            ("📱 Samsung FR", "https://www.samsung.com/fr/")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer tous les boutons
        for idx, (label, url) in enumerate(fournisseurs_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['fournisseurs'] = section_frame

    def create_securite_section(self):
        """Crée la section Sécurité & Confidentialité"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🔒 SÉCURITÉ & CONFIDENTIALITÉ", 'securite')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sites sécurité et confidentialité
        securite_buttons = [
            ("🔒 ProtonVPN", "https://protonvpn.com/"),
            ("🛡️ NordVPN", "https://nordvpn.com/"),
            ("⚡ ExpressVPN", "https://www.expressvpn.com/"),
            ("🔐 Malwarebytes", "https://www.malwarebytes.com/"),
            ("🛡️ Kaspersky Free", "https://www.kaspersky.fr/downloads/free-antivirus"),
            ("🔒 Bitdefender Free", "https://www.bitdefender.com/solutions/free.html"),
            ("🌐 Have I Been Pwned", "https://haveibeenpwned.com/"),
            ("🔐 VirusTotal", "https://www.virustotal.com/"),
            ("🛡️ Hybrid Analysis", "https://www.hybrid-analysis.com/"),
            ("🔒 Any.Run", "https://any.run/"),
            ("⚡ URLScan.io", "https://urlscan.io/"),
            ("🔐 Shodan", "https://www.shodan.io/"),
            ("🛡️ Joe Sandbox", "https://www.joesandbox.com/"),
            ("🔒 Avast Free", "https://www.avast.com/free-antivirus-download"),
            ("⚡ AVG Free", "https://www.avg.com/free-antivirus-download"),
            ("🔐 Windows Defender", "windowsdefender:"),
            ("🛡️ KeePass", "https://keepass.info/download.html"),
            ("🔒 Bitwarden", "https://bitwarden.com/download/"),
            ("⚡ 1Password", "https://1password.com/downloads/"),
            ("🔐 LastPass", "https://www.lastpass.com/download"),
            ("🛡️ VeraCrypt", "https://www.veracrypt.fr/en/Downloads.html"),
            ("🔒 Tor Browser", "https://www.torproject.org/download/"),
            ("⚡ Brave Browser", "https://brave.com/download/"),
            ("🔐 Privacy Badger", "https://privacybadger.org/"),
            ("🛡️ uBlock Origin", "https://ublockorigin.com/"),
            ("🔒 HTTPS Everywhere", "https://www.eff.org/https-everywhere"),
            ("⚡ No-IP", "https://www.noip.com/"),
            ("🔐 DuckDuckGo", "https://duckduckgo.com/"),
            ("🛡️ Startpage", "https://www.startpage.com/"),
            ("🔒 ProtonMail", "https://proton.me/mail"),
            ("⚡ Tutanota", "https://tutanota.com/"),
            ("🔐 Ghostery", "https://www.ghostery.com/"),
            ("🛡️ Disconnect", "https://disconnect.me/"),
            ("🔒 CyberGhost VPN", "https://www.cyberghostvpn.com/"),
            ("⚡ Windscribe VPN", "https://windscribe.com/")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer tous les boutons
        for idx, (label, url) in enumerate(securite_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u) if u.startswith('http') else self.execute_quick_command(u, False)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['securite'] = section_frame

    def create_benchmark_section(self):
        """Crée la section Benchmark & Tests"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "📊 BENCHMARK & TESTS", 'benchmark')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sites benchmark et tests
        benchmark_buttons = [
            ("⚡ UserBenchmark", "https://www.userbenchmark.com/"),
            ("📊 3DMark", "https://benchmarks.ul.com/3dmark"),
            ("💻 PCMark", "https://benchmarks.ul.com/pcmark10"),
            ("🔍 Geekbench", "https://www.geekbench.com/"),
            ("⚡ Cinebench", "https://www.maxon.net/en/cinebench"),
            ("📈 PassMark", "https://www.passmark.com/"),
            ("💾 CrystalDiskMark", "https://crystalmark.info/en/software/crystaldiskmark/"),
            ("📊 AS SSD Benchmark", "https://www.alex-is.de/"),
            ("⚡ ATTO Disk Benchmark", "https://www.atto.com/disk-benchmark/"),
            ("🔍 HD Tune", "https://www.hdtune.com/"),
            ("📈 Unigine Heaven", "https://benchmark.unigine.com/heaven"),
            ("💻 Unigine Valley", "https://benchmark.unigine.com/valley"),
            ("📊 Unigine Superposition", "https://benchmark.unigine.com/superposition"),
            ("⚡ FurMark", "https://geeks3d.com/furmark/"),
            ("🔍 Prime95", "https://www.mersenne.org/download/"),
            ("📈 AIDA64", "https://www.aida64.com/"),
            ("💾 MemTest86", "https://www.memtest86.com/"),
            ("📊 MemTest64", "https://www.techpowerup.com/memtest64/"),
            ("⚡ OCCT", "https://www.ocbase.com/"),
            ("🔍 Intel Burn Test", "https://www.techspot.com/downloads/4965-intel-burn-test.html"),
            ("📈 LinX", "https://www.techpowerup.com/download/linx/"),
            ("💻 Y-Cruncher", "http://www.numberworld.org/y-cruncher/"),
            ("📊 Blender Benchmark", "https://opendata.blender.org/"),
            ("⚡ V-Ray Benchmark", "https://www.chaos.com/vray/benchmark"),
            ("🔍 Basemark GPU", "https://www.basemark.com/products/basemark-gpu/"),
            ("📈 GFXBench", "https://gfxbench.com/"),
            ("💾 ADATA SSD Toolbox", "https://www.adata.com/us/ss/software-5/"),
            ("📊 Samsung Magician", "https://www.samsung.com/semiconductor/minisite/ssd/product/consumer/magician/"),
            ("⚡ Western Digital Dashboard", "https://support.wdc.com/downloads.aspx?lang=en"),
            ("🔍 Crucial Storage Executive", "https://www.crucial.com/support/storage-executive")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer tous les boutons
        for idx, (label, url) in enumerate(benchmark_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['benchmark'] = section_frame

    def create_depannage_section(self):
        """Crée la section Dépannage à Distance"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "🖥️ DÉPANNAGE À DISTANCE", 'depannage')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sites dépannage à distance
        depannage_buttons = [
            ("🖥️ TeamViewer", "https://www.teamviewer.com/fr/"),
            ("💻 AnyDesk", "https://anydesk.com/fr"),
            ("📡 Chrome Remote Desktop", "https://remotedesktop.google.com/"),
            ("🔧 RustDesk", "https://rustdesk.com/"),
            ("⚡ TightVNC", "https://www.tightvnc.com/"),
            ("🌐 UltraVNC", "https://uvnc.com/"),
            ("💼 Splashtop", "https://www.splashtop.com/"),
            ("📊 LogMeIn", "https://www.logmein.com/"),
            ("🔍 Zoho Assist", "https://www.zoho.com/assist/"),
            ("⚡ RemotePC", "https://www.remotepc.com/"),
            ("🖥️ Ammyy Admin", "https://www.ammyy.com/"),
            ("💻 ShowMyPC", "https://showmypc.com/"),
            ("📡 DWService", "https://www.dwservice.net/"),
            ("🔧 NoMachine", "https://www.nomachine.com/"),
            ("⚡ VNC Connect", "https://www.realvnc.com/fr/connect/download/viewer/"),
            ("🌐 Mikogo", "https://www.mikogo.com/"),
            ("💼 GoToMyPC", "https://www.gotomypc.com/"),
            ("📊 Connectwise Control", "https://control.connectwise.com/"),
            ("🔍 Supremo", "https://www.supremocontrol.com/"),
            ("⚡ LiteManager", "https://www.litemanager.com/"),
            ("🖥️ Microsoft Quick Assist", "ms-quick-assist:"),
            ("💻 Windows Remote Desktop", "mstsc")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer tous les boutons
        for idx, (label, cmd_or_url) in enumerate(depannage_buttons):
            row = idx // 6
            col = idx % 6
            if cmd_or_url.startswith('http') or cmd_or_url.startswith('ms-'):
                ttk.Button(
                    scrollable,
                    text=label,
                    command=lambda u=cmd_or_url: webbrowser.open(u)
                ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")
            else:
                ttk.Button(
                    scrollable,
                    text=label,
                    command=lambda c=cmd_or_url: self.execute_quick_command(c, False)
                ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['depannage'] = section_frame

    def create_drivers_section(self):
        """Crée la section Drivers & Pilotes"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "💿 DRIVERS & PILOTES", 'drivers')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sites drivers et pilotes
        drivers_buttons = [
            ("🎮 NVIDIA Drivers", "https://www.nvidia.com/Download/index.aspx"),
            ("🔴 AMD Drivers", "https://www.amd.com/en/support"),
            ("💻 Intel Drivers", "https://www.intel.com/content/www/us/en/download-center/home.html"),
            ("🖨️ HP Support", "https://support.hp.com/drivers"),
            ("💼 Dell Drivers", "https://www.dell.com/support/home/"),
            ("📱 Lenovo Support", "https://support.lenovo.com/"),
            ("🔧 ASUS Support", "https://www.asus.com/support/Download-Center/"),
            ("⚡ MSI Support", "https://www.msi.com/support/download"),
            ("🌐 Gigabyte Support", "https://www.gigabyte.com/Support"),
            ("💾 Samsung Support", "https://www.samsung.com/us/support/downloads/"),
            ("📊 Realtek", "https://www.realtek.com/en/downloads"),
            ("🔊 Creative Labs", "https://support.creative.com/"),
            ("🎵 Sound Blaster", "https://support.creative.com/products/soundblaster/"),
            ("📡 TP-Link", "https://www.tp-link.com/support/download/"),
            ("🌐 Netgear", "https://www.netgear.com/support/download/"),
            ("⚡ D-Link", "https://www.dlink.com/support/"),
            ("🖥️ Canon Drivers", "https://www.canon.com/support/"),
            ("🖨️ Epson Support", "https://epson.com/Support/sl/s"),
            ("📄 Brother Support", "https://support.brother.com/"),
            ("💼 Xerox Drivers", "https://www.xerox.com/downloads"),
            ("🔧 Logitech Support", "https://support.logi.com/"),
            ("🖱️ Razer Support", "https://support.razer.com/"),
            ("⌨️ Corsair Support", "https://www.corsair.com/support"),
            ("🎮 SteelSeries", "https://steelseries.com/downloads"),
            ("📱 Western Digital", "https://support.wdc.com/downloads.aspx"),
            ("💾 Seagate Support", "https://www.seagate.com/support/downloads/"),
            ("🔊 Focusrite", "https://focusrite.com/downloads"),
            ("🎵 Behringer", "https://www.behringer.com/downloads.html"),
            ("📡 DriverPack", "https://drp.su/"),
            ("🔍 Snappy Driver Installer", "https://sdi-tool.org/"),
            ("⚡ Driver Booster", "https://www.iobit.com/driver-booster.php"),
            ("💻 DriverEasy", "https://www.drivereasy.com/"),
            ("🔧 Driver Genius", "https://www.driver-soft.com/"),
            ("🌐 SlimDrivers", "https://www.slimwareutilities.com/slimdrivers.php")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer tous les boutons
        for idx, (label, url) in enumerate(drivers_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['drivers'] = section_frame

    def create_documentation_section(self):
        """Crée la section Documentation Technique"""
        section_frame = ttk.Frame(self.tools_paned)

        # En-tête avec drag handle
        header = self.create_draggable_header(section_frame, "📚 DOCUMENTATION TECHNIQUE", 'documentation')
        header.pack(fill="x", padx=2, pady=2)

        # Contenu avec hauteur fixe optimale
        content_frame = ttk.Frame(section_frame, height=120)
        content_frame.pack(fill="both", expand=True, padx=2)
        content_frame.pack_propagate(False)

        canvas = tk.Canvas(content_frame, bg=self.DARK_BG2, highlightthickness=0)
        scrollbar = ttk.Scrollbar(content_frame, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)

        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Sites documentation technique
        documentation_buttons = [
            ("📖 Microsoft Docs", "https://docs.microsoft.com/"),
            ("💻 TechNet", "https://technet.microsoft.com/"),
            ("🔧 Tom's Hardware", "https://www.tomshardware.com/"),
            ("⚡ AnandTech", "https://www.anandtech.com/"),
            ("📊 PCPartPicker", "https://pcpartpicker.com/"),
            ("🌐 Stack Overflow", "https://stackoverflow.com/"),
            ("💼 Super User", "https://superuser.com/"),
            ("🔍 Reddit r/techsupport", "https://www.reddit.com/r/techsupport/"),
            ("📈 Reddit r/buildapc", "https://www.reddit.com/r/buildapc/"),
            ("💾 NotebookCheck", "https://www.notebookcheck.net/"),
            ("🖥️ LaptopMag", "https://www.laptopmag.com/"),
            ("🔧 iFixit", "https://www.ifixit.com/"),
            ("⚡ LinusTechTips Forum", "https://linustechtips.com/"),
            ("📚 Wikiwand Tech", "https://www.wikiwand.com/"),
            ("💻 Wikipedia Tech", "https://en.wikipedia.org/wiki/Portal:Technology"),
            ("🌐 GitHub", "https://github.com/"),
            ("🔍 GitLab", "https://gitlab.com/"),
            ("📊 BitBucket", "https://bitbucket.org/"),
            ("⚡ DevDocs", "https://devdocs.io/"),
            ("💼 W3Schools", "https://www.w3schools.com/"),
            ("🔧 MDN Web Docs", "https://developer.mozilla.org/"),
            ("📈 Can I Use", "https://caniuse.com/"),
            ("💾 Regex101", "https://regex101.com/"),
            ("🖥️ Ninite", "https://ninite.com/"),
            ("🔍 AlternativeTo", "https://alternativeto.net/"),
            ("⚡ FileHippo", "https://filehippo.com/"),
            ("📚 Softpedia", "https://www.softpedia.com/"),
            ("💻 FileHorse", "https://www.filehorse.com/"),
            ("🌐 SourceForge", "https://sourceforge.net/"),
            ("🔧 Chocolatey", "https://chocolatey.org/"),
            ("⚡ WingetUI", "https://www.marticliment.com/wingetui/"),
            ("📊 PCGamingWiki", "https://www.pcgamingwiki.com/"),
            ("💼 ProtonDB", "https://www.protondb.com/"),
            ("🔍 ArchWiki", "https://wiki.archlinux.org/")
        ]

        # Configuration 6 colonnes
        for i in range(6):
            scrollable.grid_columnconfigure(i, weight=1)

        # Créer tous les boutons
        for idx, (label, url) in enumerate(documentation_buttons):
            row = idx // 6
            col = idx % 6
            ttk.Button(
                scrollable,
                text=label,
                command=lambda u=url: webbrowser.open(u)
            ).grid(row=row, column=col, pady=1, padx=1, sticky="ew")

        self.section_widgets['documentation'] = section_frame

    def create_draggable_header(self, parent, title, section_name):
        """Crée un en-tête draggable pour réorganiser les sections"""
        header = tk.Frame(parent, bg=self.ACCENT_BLUE, cursor="hand2", height=30)  # Bleu foncé Ordi Plus
        
        label = tk.Label(
            header, 
            text=f"⋮⋮ {title}",
            bg=self.ACCENT_BLUE,  # Bleu foncé Ordi Plus
            fg="white",
            font=('Segoe UI', 9, 'bold'),
            pady=5
        )
        label.pack(fill="both", expand=True)
        
        # Bind drag events
        header.bind("<Button-1>", lambda e: self.start_drag(e, section_name))
        header.bind("<B1-Motion>", lambda e: self.on_drag(e, section_name))
        header.bind("<ButtonRelease-1>", lambda e: self.end_drag(e, section_name))
        
        label.bind("<Button-1>", lambda e: self.start_drag(e, section_name))
        label.bind("<B1-Motion>", lambda e: self.on_drag(e, section_name))
        label.bind("<ButtonRelease-1>", lambda e: self.end_drag(e, section_name))
        
        return header
    
    def start_drag(self, event, section_name):
        """Début du drag d'une section"""
        self.drag_data = {
            'section': section_name,
            'start_y': event.y_root,
            'original_index': self.sections_order.index(section_name)
        }
    
    def on_drag(self, event, section_name):
        """Pendant le drag"""
        if hasattr(self, 'drag_data'):
            delta_y = event.y_root - self.drag_data['start_y']
            # Visuel du drag (optionnel)
            pass
    
    def end_drag(self, event, section_name):
        """Fin du drag - réorganise les sections"""
        if not hasattr(self, 'drag_data'):
            return
        
        delta_y = event.y_root - self.drag_data['start_y']
        original_index = self.drag_data['original_index']
        
        # Calculer le nouvel index basé sur le déplacement
        # Chaque section fait environ 200px
        sections_moved = round(delta_y / 200)
        new_index = max(0, min(len(self.sections_order) - 1, original_index + sections_moved))
        
        if new_index != original_index:
            # Réorganiser l'ordre
            self.sections_order.pop(original_index)
            self.sections_order.insert(new_index, section_name)
            
            # Reconstruire le PanedWindow
            self.rebuild_tools_panel()
        
        del self.drag_data
    
    def rebuild_tools_panel(self):
        """Reconstruit le panneau d'outils avec le nouvel ordre"""
        # Retirer toutes les sections
        for child in self.tools_paned.panes():
            self.tools_paned.forget(child)
        
        # Réajouter dans le nouvel ordre
        for section_name in self.sections_order:
            if section_name in self.section_widgets:
                self.tools_paned.add(self.section_widgets[section_name])
    
    def open_manufacturer_support(self, url):
        """Ouvre le lien de support du fabricant dans le navigateur"""
        import webbrowser
        try:
            webbrowser.open(url)
            self.logger.info(f"✅ Ouverture du support fabricant: {url}")
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'ouverture du lien: {e}")
            messagebox.showerror(
                "Erreur",
                f"❌ Impossible d'ouvrir le lien:\n{e}"
            )
    
    def open_download_link(self, url):
        """Ouvre le lien de téléchargement dans le navigateur"""
        import webbrowser
        try:
            if url:
                webbrowser.open(url)
                self.logger.info(f"✅ Ouverture du lien de téléchargement: {url}")
                messagebox.showinfo(
                    "Téléchargement",
                    "Le lien de téléchargement a été ouvert dans votre navigateur.\n\n"
                    "Téléchargez l'outil et exécutez-le pour désinstaller proprement l'antivirus."
                )
            else:
                messagebox.showerror(
                    "Erreur",
                    "Aucun lien de téléchargement disponible pour cet outil."
                )
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'ouverture du lien: {e}")
            messagebox.showerror(
                "Erreur",
                f"❌ Impossible d'ouvrir le lien:\n{e}"
            )
    
    def execute_quick_command(self, command, admin_required=False):
        """Exécute une commande Windows rapidement (boutons d'accès rapide)"""
        import subprocess
        
        try:
            if admin_required:
                # Confirmation pour les commandes admin
                if not messagebox.askyesno(
                    "Droits administrateur requis",
                    f"Cette commande nécessite les droits administrateur:\n\n{command}\n\n"
                    "Voulez-vous continuer ?"
                ):
                    return
                
                # Exécuter en mode administrateur avec PowerShell - FENÊTRE VISIBLE
                ps_command = f'Start-Process cmd.exe -ArgumentList "/k {command}" -Verb RunAs'
                subprocess.Popen(
                    ["powershell.exe", "-Command", ps_command],
                    shell=True
                )
                self.logger.info(f"✅ Commande admin exécutée: {command}")
                
            else:
                # Exécuter normalement - FENÊTRE VISIBLE
                subprocess.Popen(
                    ["cmd.exe", "/k", command],
                    shell=True
                )
                self.logger.info(f"✅ Commande exécutée: {command}")
                
        except Exception as e:
            self.logger.error(f"❌ Erreur lors de l'exécution de la commande: {e}")
            messagebox.showerror(
                "Erreur",
                f"❌ Impossible d'exécuter la commande:\n{e}"
            )
    
    def open_organize_dialog(self):
        """Ouvre le dialogue d'organisation des programmes avec drag & drop"""
        dialog = tk.Toplevel(self.root)
        dialog.title("🔄 Organiser les programmes")
        dialog.geometry("900x700")
        dialog.configure(bg=self.DARK_BG)
        
        # Centrer la fenêtre
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Titre
        title_label = ttk.Label(
            main_frame,
            text="🔄 Organiser les programmes - Glissez-déposez entre les catégories",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 10))
        
        # Frame pour les deux listes côte à côte
        lists_frame = ttk.Frame(main_frame)
        lists_frame.pack(fill="both", expand=True)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=1)
        
        # Variables pour le drag & drop
        self.drag_data = {"source_cat": None, "program_name": None}
        
        # Frame gauche - Catégories et programmes
        left_frame = ttk.LabelFrame(lists_frame, text="📁 Catégories et Programmes", padding=10)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        # Sélecteur de catégorie
        cat_select_frame = ttk.Frame(left_frame)
        cat_select_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(cat_select_frame, text="Catégorie:").pack(side="left", padx=(0, 10))
        
        category_var = tk.StringVar()
        categories = sorted(self.programs.keys())
        category_combo = ttk.Combobox(cat_select_frame, textvariable=category_var, values=categories, state='readonly', width=30)
        category_combo.pack(side="left", fill="x", expand=True)
        
        # Liste des programmes de la catégorie sélectionnée
        programs_list = tk.Listbox(left_frame, bg=self.DARK_BG2, fg=self.DARK_FG, height=25, selectmode=tk.SINGLE)
        programs_list.pack(fill="both", expand=True)
        
        # Scrollbar pour la liste
        scrollbar_left = ttk.Scrollbar(left_frame, orient="vertical", command=programs_list.yview)
        scrollbar_left.pack(side="right", fill="y")
        programs_list.config(yscrollcommand=scrollbar_left.set)
        
        # Frame droit - Destination
        right_frame = ttk.LabelFrame(lists_frame, text="🎯 Déplacer vers la catégorie", padding=10)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Sélecteur de catégorie destination
        dest_cat_frame = ttk.Frame(right_frame)
        dest_cat_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(dest_cat_frame, text="Catégorie destination:").pack(side="left", padx=(0, 10))
        
        dest_category_var = tk.StringVar()
        dest_category_combo = ttk.Combobox(dest_cat_frame, textvariable=dest_category_var, values=categories, state='readonly', width=30)
        dest_category_combo.pack(side="left", fill="x", expand=True)
        
        # Zone d'information
        info_text = scrolledtext.ScrolledText(right_frame, bg=self.DARK_BG2, fg=self.DARK_FG, height=25, wrap=tk.WORD)
        info_text.pack(fill="both", expand=True)
        info_text.insert("1.0", "👆 Sélectionnez un programme à gauche\n📂 Choisissez une catégorie de destination\n✅ Cliquez sur 'Déplacer' pour transférer")
        info_text.config(state='disabled')
        
        # Fonction pour charger les programmes d'une catégorie
        def load_programs(event=None):
            programs_list.delete(0, tk.END)
            cat = category_var.get()
            if cat and cat in self.programs:
                for prog_name in sorted(self.programs[cat].keys()):
                    programs_list.insert(tk.END, prog_name)
        
        category_combo.bind("<<ComboboxSelected>>", load_programs)
        
        # Charger la première catégorie par défaut
        if categories:
            category_combo.current(0)
            load_programs()
        
        # Fonction de déplacement
        def move_program():
            selection = programs_list.curselection()
            if not selection:
                messagebox.showwarning("Sélection requise", "Veuillez sélectionner un programme à déplacer.")
                return
            
            source_cat = category_var.get()
            dest_cat = dest_category_var.get()
            program_name = programs_list.get(selection[0])
            
            if not dest_cat:
                messagebox.showwarning("Destination requise", "Veuillez sélectionner une catégorie de destination.")
                return
            
            if source_cat == dest_cat:
                messagebox.showinfo("Même catégorie", "Le programme est déjà dans cette catégorie.")
                return
            
            # Confirmation
            if not messagebox.askyesno("Confirmer", f"Déplacer '{program_name}'\nDe: {source_cat}\nVers: {dest_cat}\n\nContinuer?"):
                return
            
            try:
                # Charger programs.json
                import sys
                if getattr(sys, 'frozen', False):
                    base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
                else:
                    base_path = Path(__file__).parent.parent
                
                programs_file = base_path / 'data' / 'programs.json'
                with open(programs_file, 'r', encoding='utf-8') as f:
                    all_programs = json.load(f)
                
                # Déplacer le programme
                program_data = all_programs[source_cat].pop(program_name)
                
                if dest_cat not in all_programs:
                    all_programs[dest_cat] = {}
                
                all_programs[dest_cat][program_name] = program_data
                
                # Sauvegarder
                with open(programs_file, 'w', encoding='utf-8') as f:
                    json.dump(all_programs, f, indent=4, ensure_ascii=False)
                
                # Mettre à jour l'affichage
                self.programs = all_programs
                load_programs()
                
                messagebox.showinfo("Succès", f"✅ '{program_name}' déplacé vers '{dest_cat}'!\n\nRedémarrez l'application pour voir les changements.")
                
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Erreur lors du déplacement:\n{e}")
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(10, 0))
        
        ttk.Button(button_frame, text="➡️ Déplacer", command=move_program, style='Action.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="🔄 Rafraîchir", command=load_programs).pack(side="left", padx=5)
        ttk.Button(button_frame, text="❌ Fermer", command=dialog.destroy).pack(side="right", padx=5)
    
    def add_custom_program(self):
        """Permet d'ajouter un programme personnalisé via URL de téléchargement"""
        dialog = tk.Toplevel(self.root)
        dialog.title("➕ Ajouter un programme personnalisé")
        dialog.geometry("600x400")
        dialog.configure(bg=self.DARK_BG)
        dialog.resizable(False, False)
        
        # Centrer la fenêtre
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Frame principal
        main_frame = ttk.Frame(dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Titre
        title_label = ttk.Label(
            main_frame,
            text="➕ Ajouter un nouveau programme",
            style='Title.TLabel'
        )
        title_label.pack(pady=(0, 20))
        
        # Nom du programme
        ttk.Label(main_frame, text="📝 Nom du programme:").pack(anchor="w", pady=(0, 5))
        name_entry = ttk.Entry(main_frame, width=60)
        name_entry.pack(fill="x", pady=(0, 15))
        
        # URL de téléchargement
        ttk.Label(main_frame, text="🔗 URL de téléchargement (.exe, .msi):").pack(anchor="w", pady=(0, 5))
        url_entry = ttk.Entry(main_frame, width=60)
        url_entry.pack(fill="x", pady=(0, 15))
        
        # Catégorie
        ttk.Label(main_frame, text="📁 Catégorie:").pack(anchor="w", pady=(0, 5))
        category_var = tk.StringVar(value="Utilitaires")
        categories = sorted(self.programs.keys())
        category_combo = ttk.Combobox(main_frame, textvariable=category_var, values=categories, width=57, state='readonly')
        category_combo.pack(fill="x", pady=(0, 15))
        
        # Description
        ttk.Label(main_frame, text="📄 Description (optionnelle):").pack(anchor="w", pady=(0, 5))
        desc_entry = ttk.Entry(main_frame, width=60)
        desc_entry.pack(fill="x", pady=(0, 20))
        
        # Boutons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")
        
        def save_program():
            name = name_entry.get().strip()
            url = url_entry.get().strip()
            category = category_var.get()
            description = desc_entry.get().strip() or name
            
            if not name or not url:
                messagebox.showwarning("Champs manquants", "Veuillez remplir le nom et l'URL du programme.")
                return
            
            if not url.startswith(('http://', 'https://')):
                messagebox.showwarning("URL invalide", "L'URL doit commencer par http:// ou https://")
                return
            
            # Ajouter le programme à programs.json
            try:
                import sys
                if getattr(sys, 'frozen', False):
                    base_path = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else Path(sys.executable).parent
                else:
                    base_path = Path(__file__).parent.parent
                
                programs_file = base_path / 'data' / 'programs.json'
                with open(programs_file, 'r', encoding='utf-8') as f:
                    all_programs = json.load(f)
                
                # Créer l'entrée du programme
                program_entry = {
                    "name": name,
                    "description": description,
                    "url": url,
                    "installer_type": "direct",
                    "silent_args": "/S",
                    "essential": False
                }
                
                # Ajouter à la catégorie
                if category not in all_programs:
                    all_programs[category] = {}
                
                all_programs[category][name] = program_entry
                
                # Sauvegarder
                with open(programs_file, 'w', encoding='utf-8') as f:
                    json.dump(all_programs, f, indent=4, ensure_ascii=False)
                
                messagebox.showinfo("Succès", f"✅ Programme '{name}' ajouté avec succès!\n\nRedémarrez l'application pour voir les changements.")
                dialog.destroy()
                
            except Exception as e:
                messagebox.showerror("Erreur", f"❌ Erreur lors de l'ajout:\n{e}")
        
        ttk.Button(button_frame, text="✅ Ajouter", command=save_program, style='Action.TButton').pack(side="left", padx=5)
        ttk.Button(button_frame, text="❌ Annuler", command=dialog.destroy).pack(side="left", padx=5)
    
    def on_closing(self):
        """Fermeture propre de l'application avec arrêt des processus enfants"""
        import sys
        import gc

        try:
            # Arrêter toute installation en cours
            if self.is_installing:
                if not messagebox.askyesno(
                    "Installation en cours",
                    "Une installation est en cours. Voulez-vous vraiment quitter ?"
                ):
                    return

            # Arrêter proprement tous les processus enfants avec psutil
            try:
                import psutil
                import os

                # Afficher message d'arrêt des processus
                if hasattr(self, 'selection_label'):
                    self.selection_label.config(text="Arrêt des processus en cours...")
                    self.root.update_idletasks()

                current_process = psutil.Process(os.getpid())
                children = current_process.children(recursive=True)

                if children:
                    self.logger.info(f"Arrêt de {len(children)} processus enfant(s)...")

                    # Terminer proprement chaque processus enfant
                    for child in children:
                        try:
                            child.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    # Attendre que les processus se terminent (max 3 secondes)
                    gone, alive = psutil.wait_procs(children, timeout=3)

                    # Forcer l'arrêt des processus qui ne se sont pas terminés
                    for p in alive:
                        try:
                            p.kill()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

                    self.logger.info(f"✅ Processus enfants arrêtés proprement")

            except ImportError:
                self.logger.warning("psutil non disponible - arrêt basique")
            except Exception as e:
                self.logger.error(f"Erreur lors de l'arrêt des processus: {e}")

            # Fermer tous les logs
            logging.shutdown()
            
            # Nettoyer les références
            self.program_vars.clear()
            self.programs.clear()
            self.category_frames.clear()
            self.category_widgets.clear()
            
            # Forcer le garbage collector
            gc.collect()
            
            # Détruire la fenêtre
            self.root.quit()
            self.root.destroy()
            
            # Forcer la sortie
            sys.exit(0)
            
        except Exception as e:
            print(f"Erreur lors de la fermeture: {e}")
            sys.exit(0)

    # ===============================================
    # MÉTHODES BASE DE DONNÉES PORTABLE
    # ===============================================
    
    def show_portable_database_stats(self):
        """Affiche les statistiques de la base de données portable"""
        from tkinter import messagebox, scrolledtext
        import tkinter as tk
        from tkinter import ttk
        
        if not self.installer_manager or not hasattr(self.installer_manager, 'portable_db') or not self.installer_manager.portable_db:
            messagebox.showinfo(
                "Base de données portable",
                "💾 La base de données portable n'est pas disponible.\n\n"
                "Elle sera créée automatiquement lors de l'installation d'applications portables."
            )
            return
        
        try:
            db = self.installer_manager.portable_db
            stats = db.get_statistics()
            categories = db.get_categories()
            
            # Créer une fenêtre de dialogue
            dialog = tk.Toplevel(self.root)
            dialog.title("💾 Base de Données Portable - Statistiques")
            dialog.geometry("700x600")
            dialog.configure(bg=self.DARK_BG)
            dialog.transient(self.root)
            dialog.grab_set()
            
            # Frame principal
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill="both", expand=True, padx=20, pady=20)
            
            # Titre
            title_label = tk.Label(
                main_frame,
                text="📊 STATISTIQUES BASE DE DONNÉES PORTABLE",
                font=('Segoe UI', 16, 'bold'),
                bg=self.DARK_BG,
                fg=self.ACCENT_ORANGE
            )
            title_label.pack(pady=(0, 20))
            
            # Frame pour les statistiques
            stats_frame = ttk.LabelFrame(main_frame, text=" 📈 Statistiques globales ", padding=15)
            stats_frame.pack(fill="x", pady=10)
            
            # Statistiques générales
            stats_text = f"""
📦 Applications totales : {stats.get('total_apps', 0)}
✅ Applications portables : {stats.get('portable_apps', 0)}
💿 Applications installées : {stats.get('installed_apps', 0)}
📁 Catégories : {len(categories)}

💾 ESPACE UTILISÉ :
   • Total : {stats.get('total_size_gb', 0):.2f} GB
   • Détails : {stats.get('total_size_mb', 0):.2f} MB
   • Octets : {stats.get('total_size_bytes', 0):,}
"""
            
            stats_label = tk.Label(
                stats_frame,
                text=stats_text,
                font=('Consolas', 10),
                bg=self.DARK_BG2,
                fg=self.DARK_FG,
                justify="left",
                anchor="w"
            )
            stats_label.pack(fill="x")
            
            # Frame pour les catégories
            cat_frame = ttk.LabelFrame(main_frame, text=" 📁 Applications par catégorie ", padding=15)
            cat_frame.pack(fill="both", expand=True, pady=10)
            
            # Créer un canvas avec scrollbar pour les catégories
            cat_canvas = tk.Canvas(cat_frame, bg=self.DARK_BG2, height=200)
            cat_scrollbar = ttk.Scrollbar(cat_frame, orient="vertical", command=cat_canvas.yview)
            cat_scrollable = ttk.Frame(cat_canvas)
            
            cat_scrollable.bind(
                "<Configure>",
                lambda e: cat_canvas.configure(scrollregion=cat_canvas.bbox("all"))
            )
            
            cat_canvas.create_window((0, 0), window=cat_scrollable, anchor="nw")
            cat_canvas.configure(yscrollcommand=cat_scrollbar.set)
            
            cat_canvas.pack(side="left", fill="both", expand=True)
            cat_scrollbar.pack(side="right", fill="y")
            
            # Afficher les catégories
            apps_by_cat = stats.get('apps_by_category', {})
            if apps_by_cat:
                for idx, (category, count) in enumerate(sorted(apps_by_cat.items(), key=lambda x: x[1], reverse=True)):
                    cat_label = tk.Label(
                        cat_scrollable,
                        text=f"  • {category}: {count} app(s)",
                        font=('Consolas', 9),
                        bg=self.DARK_BG2,
                        fg=self.DARK_FG2,
                        anchor="w"
                    )
                    cat_label.pack(fill="x", pady=2)
            else:
                no_cat_label = tk.Label(
                    cat_scrollable,
                    text="Aucune catégorie pour le moment",
                    font=('Consolas', 9),
                    bg=self.DARK_BG2,
                    fg=self.ACCENT_YELLOW,
                    anchor="w"
                )
                no_cat_label.pack(fill="x", pady=2)
            
            # Boutons d'action
            button_frame = ttk.Frame(main_frame)
            button_frame.pack(fill="x", pady=(20, 0))
            
            ttk.Button(
                button_frame,
                text="🔍 Voir toutes les apps",
                command=lambda: self.show_all_portable_apps(dialog),
                style='Action.TButton'
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="🔐 Vérifier intégrité",
                command=lambda: self.verify_database_integrity(dialog)
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="📤 Exporter JSON",
                command=lambda: self.export_database_json(dialog)
            ).pack(side="left", padx=5)
            
            ttk.Button(
                button_frame,
                text="❌ Fermer",
                command=dialog.destroy
            ).pack(side="right", padx=5)
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'affichage des statistiques: {e}")
            messagebox.showerror(
                "Erreur",
                f"❌ Impossible d'afficher les statistiques:\n\n{e}"
            )

    def show_all_portable_apps(self, parent_dialog=None):
        """Affiche toutes les applications portables de la base de données"""
        from tkinter import scrolledtext
        import tkinter as tk
        from tkinter import ttk
        
        if not self.installer_manager or not self.installer_manager.portable_db:
            return
        
        try:
            db = self.installer_manager.portable_db
            apps = db.list_applications(portable_only=True)
            
            # Créer une fenêtre
            dialog = tk.Toplevel(parent_dialog or self.root)
            dialog.title(f"📦 Applications Portables ({len(apps)})")
            dialog.geometry("900x600")
            dialog.configure(bg=self.DARK_BG)
            
            # Frame principal
            main_frame = ttk.Frame(dialog)
            main_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Titre
            title_label = tk.Label(
                main_frame,
                text=f"📦 {len(apps)} APPLICATIONS PORTABLES",
                font=('Segoe UI', 14, 'bold'),
                bg=self.DARK_BG,
                fg=self.ACCENT_GREEN
            )
            title_label.pack(pady=(0, 10))
            
            # Zone de texte avec scrollbar
            text_frame = ttk.Frame(main_frame)
            text_frame.pack(fill="both", expand=True)
            
            text_widget = scrolledtext.ScrolledText(
                text_frame,
                font=('Consolas', 9),
                bg=self.DARK_BG2,
                fg=self.DARK_FG,
                wrap="word"
            )
            text_widget.pack(fill="both", expand=True)
            
            # Afficher les applications
            for app in apps:
                text_widget.insert("end", f"📦 {app['name']}\n", "app_name")
                text_widget.insert("end", f"   Catégorie: {app.get('category', 'N/A')}\n")
                text_widget.insert("end", f"   Description: {app.get('description', 'N/A')}\n")
                text_widget.insert("end", f"   Version: {app.get('version', 'N/A')}\n")
                text_widget.insert("end", f"   Chemin: {app.get('executable_path', 'N/A')}\n")
                size_mb = app.get('file_size', 0) / 1024 / 1024 if app.get('file_size') else 0
                text_widget.insert("end", f"   Taille: {size_mb:.2f} MB\n")
                text_widget.insert("end", "\n" + "-"*80 + "\n\n")
            
            text_widget.configure(state="disabled")
            
            # Bouton fermer
            ttk.Button(
                main_frame,
                text="❌ Fermer",
                command=dialog.destroy
            ).pack(pady=(10, 0))
            
        except Exception as e:
            self.logger.error(f"Erreur lors de l'affichage des apps: {e}")
            messagebox.showerror("Erreur", f"❌ Erreur:\n{e}")

    def verify_database_integrity(self, parent_dialog=None):
        """Vérifie l'intégrité de la base de données"""
        from tkinter import messagebox, scrolledtext
        import tkinter as tk
        from tkinter import ttk
        
        if not self.installer_manager or not self.installer_manager.portable_db:
            return
        
        try:
            db = self.installer_manager.portable_db
            issues = db.verify_integrity()
            
            if not issues:
                messagebox.showinfo(
                    "Vérification d'intégrité",
                    "✅ AUCUN PROBLÈME DÉTECTÉ\n\n"
                    "La base de données est intègre.\n"
                    "Tous les fichiers sont présents et non modifiés."
                )
            else:
                # Créer une fenêtre pour afficher les problèmes
                dialog = tk.Toplevel(parent_dialog or self.root)
                dialog.title(f"⚠️ Problèmes détectés ({len(issues)})")
                dialog.geometry("700x400")
                dialog.configure(bg=self.DARK_BG)
                
                main_frame = ttk.Frame(dialog)
                main_frame.pack(fill="both", expand=True, padx=10, pady=10)
                
                title_label = tk.Label(
                    main_frame,
                    text=f"⚠️ {len(issues)} PROBLÈME(S) DÉTECTÉ(S)",
                    font=('Segoe UI', 12, 'bold'),
                    bg=self.DARK_BG,
                    fg=self.ACCENT_RED
                )
                title_label.pack(pady=(0, 10))
                
                text_widget = scrolledtext.ScrolledText(
                    main_frame,
                    font=('Consolas', 9),
                    bg=self.DARK_BG2,
                    fg=self.DARK_FG
                )
                text_widget.pack(fill="both", expand=True)
                
                for issue in issues:
                    text_widget.insert("end", f"⚠️ {issue['app']}\n", "app_name")
                    text_widget.insert("end", f"   Problème: {issue['issue']}\n")
                    text_widget.insert("end", f"   Chemin: {issue['path']}\n\n")
                
                text_widget.configure(state="disabled")
                
                ttk.Button(main_frame, text="❌ Fermer", command=dialog.destroy).pack(pady=(10, 0))
                
        except Exception as e:
            self.logger.error(f"Erreur lors de la vérification: {e}")
            messagebox.showerror("Erreur", f"❌ Erreur:\n{e}")

    def export_database_json(self, parent_dialog=None):
        """Exporte la base de données vers un fichier JSON"""
        from tkinter import messagebox, filedialog
        from datetime import datetime
        
        if not self.installer_manager or not self.installer_manager.portable_db:
            return
        
        try:
            # Demander où sauvegarder
            default_name = f"portable_apps_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            filename = filedialog.asksaveasfilename(
                parent=parent_dialog or self.root,
                title="Exporter la base de données",
                defaultextension=".json",
                initialfile=default_name,
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if filename:
                db = self.installer_manager.portable_db
                success = db.export_to_json(filename)
                
                if success:
                    messagebox.showinfo(
                        "Export réussi",
                        f"✅ Base de données exportée avec succès!\n\n"
                        f"Fichier: {filename}"
                    )
                else:
                    messagebox.showerror(
                        "Erreur d'export",
                        "❌ Impossible d'exporter la base de données."
                    )
        except Exception as e:
            self.logger.error(f"Erreur lors de l'export: {e}")
            messagebox.showerror("Erreur", f"❌ Erreur:\n{e}")


def create_gui_manager(root, installer_manager=None, config_manager=None):
    """Crée et retourne le GUI Manager complet"""
    return NiTriteGUIComplet(root, installer_manager, config_manager)
