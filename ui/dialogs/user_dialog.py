"""
PolicyHub User Dialog (PySide6)

Dialog for adding and editing users.
"""

from typing import List, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QFrame,
    QScrollArea,
)

from app.constants import UserRole
from app.theme import COLORS, SPACING, TYPOGRAPHY, style_button
from core.database import DatabaseManager
from ui.dialogs.base_dialog import BaseDialog
from ui.dialogs.confirm_dialog import InfoDialog
from models.user import User, UserCreate, UserUpdate
from services.category_service import CategoryService
from services.entity_service import EntityService
from services.user_service import UserService
from utils.validators import validate_email, validate_password, validate_username


class UserDialog(BaseDialog):
    """
    Dialog for adding or editing a user.

    In add mode: Shows all fields including password
    In edit mode: Hides password field (use Reset Password separately)
    """

    def __init__(
        self,
        parent: QWidget,
        db: DatabaseManager,
        user: Optional[User] = None,
    ):
        """
        Initialize the user dialog.

        Args:
            parent: Parent window
            db: Database manager
            user: User to edit (None for add mode)
        """
        self.db = db
        self.user_service = UserService(db)
        self.category_service = CategoryService(db)
        self.entity_service = EntityService(db)
        self.user = user
        self.is_edit_mode = user is not None

        # Track selected restrictions
        self._category_checkboxes: dict = {}
        self._entity_checkboxes: dict = {}

        title = "Edit User" if self.is_edit_mode else "Add User"
        height = 600 if self.is_edit_mode else 680

        super().__init__(parent, title, width=500, height=height)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
            SPACING.WINDOW_PADDING,
        )
        layout.setSpacing(0)

        # Scrollable form
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        form = QWidget()
        form.setStyleSheet("background: transparent;")
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(0, 0, 0, 0)
        form_layout.setSpacing(12)

        # Username field
        self._create_label(form_layout, "Username *")
        self.username_entry = QLineEdit()
        self.username_entry.setFixedWidth(300)
        self.username_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.username_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.username_entry)
        form_layout.addWidget(self.username_entry)

        if self.is_edit_mode:
            self.username_entry.setText(self.user.username)
            self.username_entry.setEnabled(False)

        # Full Name field
        self._create_label(form_layout, "Full Name *")
        self.fullname_entry = QLineEdit()
        self.fullname_entry.setFixedWidth(300)
        self.fullname_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.fullname_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.fullname_entry)
        form_layout.addWidget(self.fullname_entry)

        if self.is_edit_mode:
            self.fullname_entry.setText(self.user.full_name)

        # Email field
        self._create_label(form_layout, "Email *")
        self.email_entry = QLineEdit()
        self.email_entry.setFixedWidth(300)
        self.email_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
        self.email_entry.setFont(TYPOGRAPHY.body)
        self._style_input(self.email_entry)
        form_layout.addWidget(self.email_entry)

        if self.is_edit_mode and self.user.email:
            self.email_entry.setText(self.user.email)

        # Role dropdown
        self._create_label(form_layout, "Role *")
        self.role_dropdown = QComboBox()
        self.role_dropdown.addItems([r.display_name for r in UserRole])
        self.role_dropdown.setFixedWidth(200)
        self.role_dropdown.setFont(TYPOGRAPHY.body)
        self._style_dropdown(self.role_dropdown)
        self.role_dropdown.currentTextChanged.connect(self._on_role_changed)
        form_layout.addWidget(self.role_dropdown)

        if self.is_edit_mode:
            try:
                role = UserRole(self.user.role)
                index = self.role_dropdown.findText(role.display_name)
                if index >= 0:
                    self.role_dropdown.setCurrentIndex(index)
            except ValueError:
                pass

        # Restrictions section
        self.restrictions_frame = QFrame()
        self.restrictions_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS.MUTED};
                border-radius: 8px;
            }}
        """)
        self._build_restrictions_section()
        form_layout.addWidget(self.restrictions_frame)

        # Password fields (only in add mode)
        if not self.is_edit_mode:
            self._create_label(form_layout, "Password *")
            self.password_entry = QLineEdit()
            self.password_entry.setFixedWidth(300)
            self.password_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
            self.password_entry.setFont(TYPOGRAPHY.body)
            self.password_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self._style_input(self.password_entry)
            form_layout.addWidget(self.password_entry)

            self._create_label(form_layout, "Confirm Password *")
            self.confirm_entry = QLineEdit()
            self.confirm_entry.setFixedWidth(300)
            self.confirm_entry.setFixedHeight(SPACING.INPUT_HEIGHT)
            self.confirm_entry.setFont(TYPOGRAPHY.body)
            self.confirm_entry.setEchoMode(QLineEdit.EchoMode.Password)
            self._style_input(self.confirm_entry)
            form_layout.addWidget(self.confirm_entry)

            hint = QLabel("Minimum 8 characters")
            hint.setFont(TYPOGRAPHY.small)
            hint.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
            form_layout.addWidget(hint)

            info_label = QLabel("Note: User will be required to change password on first login.")
            info_label.setFont(TYPOGRAPHY.small)
            info_label.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
            info_label.setWordWrap(True)
            form_layout.addWidget(info_label)

        # Active checkbox (only in edit mode)
        if self.is_edit_mode:
            self.active_checkbox = QCheckBox("Account is active")
            self.active_checkbox.setFont(TYPOGRAPHY.body)
            self.active_checkbox.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            self.active_checkbox.setChecked(self.user.is_active)
            form_layout.addWidget(self.active_checkbox)

        form_layout.addStretch()
        scroll.setWidget(form)
        layout.addWidget(scroll, 1)

        # Buttons
        btn_frame = QWidget()
        btn_frame.setStyleSheet("background: transparent;")
        btn_layout = QHBoxLayout(btn_frame)
        btn_layout.setContentsMargins(0, 16, 0, 0)
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFixedSize(100, 36)
        style_button(cancel_btn, "secondary")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save" if self.is_edit_mode else "Create User")
        save_btn.setFixedSize(120, 36)
        style_button(save_btn, "primary")
        save_btn.clicked.connect(self._on_save)
        btn_layout.addWidget(save_btn)

        layout.addWidget(btn_frame)

        # Update restrictions visibility
        self._on_role_changed(self.role_dropdown.currentText())

    def _create_label(self, layout: QVBoxLayout, text: str) -> None:
        """Create a field label."""
        label = QLabel(text)
        label.setFont(TYPOGRAPHY.body)
        label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(label)

    def _style_input(self, widget: QLineEdit) -> None:
        """Apply input styling."""
        widget.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 0 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border-color: {COLORS.PRIMARY};
            }}
            QLineEdit:disabled {{
                background-color: {COLORS.MUTED};
                color: {COLORS.TEXT_MUTED};
            }}
        """)

    def _style_dropdown(self, widget: QComboBox) -> None:
        """Apply dropdown styling."""
        widget.setStyleSheet(f"""
            QComboBox {{
                background-color: {COLORS.BACKGROUND};
                border: 1px solid {COLORS.BORDER};
                border-radius: 4px;
                padding: 6px 12px;
                color: {COLORS.TEXT_PRIMARY};
            }}
            QComboBox:hover {{
                border-color: {COLORS.PRIMARY};
            }}
            QComboBox QAbstractItemView {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.BORDER};
                selection-background-color: {COLORS.PRIMARY};
                selection-color: {COLORS.PRIMARY_FOREGROUND};
            }}
        """)

    def _build_restrictions_section(self) -> None:
        """Build the restrictions section for EDITOR_RESTRICTED role."""
        layout = QVBoxLayout(self.restrictions_frame)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        header = QLabel("Access Restrictions")
        header.setFont(TYPOGRAPHY.section_heading)
        header.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(header)

        # Description
        desc = QLabel("User can edit documents matching ANY selected category OR entity.")
        desc.setFont(TYPOGRAPHY.small)
        desc.setStyleSheet(f"color: {COLORS.TEXT_SECONDARY}; background: transparent;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        # Vertical layout - Categories section (above)
        cat_label = QLabel("Allowed Categories:")
        cat_label.setFont(TYPOGRAPHY.small)
        cat_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(cat_label)

        # Search box for categories
        self.cat_search = QLineEdit()
        self.cat_search.setPlaceholderText("Search categories...")
        self.cat_search.setFont(TYPOGRAPHY.small)
        self.cat_search.setFixedHeight(28)
        self.cat_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.INPUT_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        self.cat_search.textChanged.connect(self._on_category_search)
        layout.addWidget(self.cat_search)

        cat_scroll = QScrollArea()
        cat_scroll.setWidgetResizable(True)
        cat_scroll.setFixedHeight(100)
        cat_scroll.setStyleSheet(f"background-color: {COLORS.CARD}; border: 1px solid {COLORS.BORDER}; border-radius: 4px;")

        self.cat_content = QWidget()
        self.cat_content.setStyleSheet("background: transparent;")
        self.cat_content_layout = QVBoxLayout(self.cat_content)
        self.cat_content_layout.setContentsMargins(8, 8, 8, 8)
        self.cat_content_layout.setSpacing(4)

        categories = self.category_service.get_all_categories()
        for cat in categories:
            cb = QCheckBox(f"{cat.code} - {cat.name}")
            cb.setFont(TYPOGRAPHY.small)
            cb.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
            self._category_checkboxes[cat.code] = cb
            self.cat_content_layout.addWidget(cb)

        self.cat_content_layout.addStretch()
        cat_scroll.setWidget(self.cat_content)
        layout.addWidget(cat_scroll)

        # Vertical layout - Entities section (below)
        ent_label = QLabel("Allowed Entities:")
        ent_label.setFont(TYPOGRAPHY.small)
        ent_label.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
        layout.addWidget(ent_label)

        # Search box for entities
        self.ent_search = QLineEdit()
        self.ent_search.setPlaceholderText("Search entities...")
        self.ent_search.setFont(TYPOGRAPHY.small)
        self.ent_search.setFixedHeight(28)
        self.ent_search.setStyleSheet(f"""
            QLineEdit {{
                background-color: {COLORS.CARD};
                border: 1px solid {COLORS.INPUT_BORDER};
                border-radius: 4px;
                padding: 4px 8px;
                color: {COLORS.TEXT_PRIMARY};
            }}
        """)
        self.ent_search.textChanged.connect(self._on_entity_search)
        layout.addWidget(self.ent_search)

        ent_scroll = QScrollArea()
        ent_scroll.setWidgetResizable(True)
        ent_scroll.setFixedHeight(100)
        ent_scroll.setStyleSheet(f"background-color: {COLORS.CARD}; border: 1px solid {COLORS.BORDER}; border-radius: 4px;")

        self.ent_content = QWidget()
        self.ent_content.setStyleSheet("background: transparent;")
        self.ent_content_layout = QVBoxLayout(self.ent_content)
        self.ent_content_layout.setContentsMargins(8, 8, 8, 8)
        self.ent_content_layout.setSpacing(4)

        entities = self.entity_service.get_all_entities()
        if entities:
            for entity in entities:
                cb = QCheckBox(entity.name)
                cb.setFont(TYPOGRAPHY.small)
                cb.setStyleSheet(f"color: {COLORS.TEXT_PRIMARY}; background: transparent;")
                self._entity_checkboxes[entity.name] = cb
                self.ent_content_layout.addWidget(cb)
        else:
            no_ent = QLabel("No entities defined yet")
            no_ent.setFont(TYPOGRAPHY.small)
            no_ent.setStyleSheet(f"color: {COLORS.TEXT_MUTED}; background: transparent;")
            self.ent_content_layout.addWidget(no_ent)

        self.ent_content_layout.addStretch()
        ent_scroll.setWidget(self.ent_content)
        layout.addWidget(ent_scroll)

        # Load existing restrictions if editing
        if self.is_edit_mode and self.user.role == UserRole.EDITOR_RESTRICTED.value:
            self._load_restrictions()

    def _on_category_search(self, text: str) -> None:
        """Filter categories by search text."""
        search_text = text.lower().strip()
        for code, cb in self._category_checkboxes.items():
            cb_text = cb.text().lower()
            cb.setVisible(search_text in cb_text)

    def _on_entity_search(self, text: str) -> None:
        """Filter entities by search text."""
        search_text = text.lower().strip()
        for name, cb in self._entity_checkboxes.items():
            cb_text = cb.text().lower()
            cb.setVisible(search_text in cb_text)

    def _on_role_changed(self, role_display: str) -> None:
        """Handle role dropdown change."""
        if role_display == UserRole.EDITOR_RESTRICTED.display_name:
            self.restrictions_frame.setVisible(True)
        else:
            self.restrictions_frame.setVisible(False)

    def _load_restrictions(self) -> None:
        """Load existing restrictions for the user."""
        if not self.user:
            return

        restrictions = self.user_service.get_user_restrictions(self.user.user_id)

        for code in restrictions["categories"]:
            if code in self._category_checkboxes:
                self._category_checkboxes[code].setChecked(True)

        for name in restrictions["entities"]:
            if name in self._entity_checkboxes:
                self._entity_checkboxes[name].setChecked(True)

    def _get_selected_categories(self) -> List[str]:
        """Get list of selected category codes."""
        return [code for code, cb in self._category_checkboxes.items() if cb.isChecked()]

    def _get_selected_entities(self) -> List[str]:
        """Get list of selected entity names."""
        return [name for name, cb in self._entity_checkboxes.items() if cb.isChecked()]

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate username
        username = self.username_entry.text().strip()
        if not self.is_edit_mode:
            is_valid, error = validate_username(username)
            if not is_valid:
                InfoDialog.show_error(self, "Invalid Username", error)
                return

            if self.user_service.username_exists(username):
                InfoDialog.show_error(self, "Username Taken", f"Username '{username}' is already in use.")
                return

        # Validate full name
        full_name = self.fullname_entry.text().strip()
        if not full_name or len(full_name) < 2:
            InfoDialog.show_error(self, "Invalid Name", "Please enter a full name (at least 2 characters).")
            return

        # Validate email
        email = self.email_entry.text().strip()
        if not email:
            InfoDialog.show_error(self, "Email Required", "Please enter an email address.")
            return

        is_valid, error = validate_email(email)
        if not is_valid:
            InfoDialog.show_error(self, "Invalid Email", error)
            return

        exclude_id = self.user.user_id if self.is_edit_mode else None
        if self.user_service.email_exists(email, exclude_user_id=exclude_id):
            InfoDialog.show_error(self, "Email Taken", f"Email '{email}' is already in use.")
            return

        # Get role
        role_display = self.role_dropdown.currentText()
        role_value = UserRole.VIEWER.value
        for r in UserRole:
            if r.display_name == role_display:
                role_value = r.value
                break

        # Validate password (add mode only)
        if not self.is_edit_mode:
            password = self.password_entry.text()
            confirm = self.confirm_entry.text()

            is_valid, error = validate_password(password)
            if not is_valid:
                InfoDialog.show_error(self, "Invalid Password", error)
                return

            if password != confirm:
                InfoDialog.show_error(self, "Password Mismatch", "Passwords do not match.")
                return

        # Validate restrictions for EDITOR_RESTRICTED
        if role_value == UserRole.EDITOR_RESTRICTED.value:
            selected_categories = self._get_selected_categories()
            selected_entities = self._get_selected_entities()
            if not selected_categories and not selected_entities:
                InfoDialog.show_error(
                    self,
                    "Restrictions Required",
                    "Please select at least one category or entity for the restricted editor.",
                )
                return

        try:
            if self.is_edit_mode:
                update_data = UserUpdate(
                    full_name=full_name,
                    email=email,
                    role=role_value,
                    is_active=self.active_checkbox.isChecked(),
                )
                self.user_service.update_user(self.user.user_id, update_data)

                if role_value == UserRole.EDITOR_RESTRICTED.value:
                    self.user_service.set_user_restrictions(
                        self.user.user_id,
                        self._get_selected_categories(),
                        self._get_selected_entities(),
                    )
                else:
                    self.user_service.clear_user_restrictions(self.user.user_id)

                self.result = True
            else:
                create_data = UserCreate(
                    username=username,
                    password=password,
                    full_name=full_name,
                    email=email,
                    role=role_value,
                )
                created_user = self.user_service.create_user(create_data)

                if role_value == UserRole.EDITOR_RESTRICTED.value and created_user:
                    self.user_service.set_user_restrictions(
                        created_user.user_id,
                        self._get_selected_categories(),
                        self._get_selected_entities(),
                    )

                self.result = True

            self.accept()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to manage users.")
        except ValueError as e:
            InfoDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))
