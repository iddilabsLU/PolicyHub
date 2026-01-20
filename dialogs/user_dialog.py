"""
PolicyHub User Dialog

Dialog for adding and editing users.
"""

from typing import List, Optional

import customtkinter as ctk

from app.constants import UserRole
from app.theme import (
    COLORS,
    SPACING,
    TYPOGRAPHY,
    configure_button_style,
    configure_dropdown_style,
    configure_input_style,
)
from core.database import DatabaseManager
from dialogs.base_dialog import BaseDialog
from dialogs.confirm_dialog import InfoDialog
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
        parent,
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
        self._selected_categories: List[str] = []
        self._selected_entities: List[str] = []
        self._category_vars: dict = {}
        self._entity_vars: dict = {}

        title = "Edit User" if self.is_edit_mode else "Add User"
        # Increased height to accommodate restrictions section
        # Taller for new users (password fields) and when restrictions might show
        height = 600 if self.is_edit_mode else 680

        super().__init__(parent, title, width=500, height=height, resizable=True)
        self._build_ui()

    def _build_ui(self) -> None:
        """Build the dialog UI."""
        # Scrollable form container
        form = ctk.CTkScrollableFrame(self, fg_color="transparent")
        form.pack(fill="both", expand=True, padx=SPACING.WINDOW_PADDING, pady=SPACING.WINDOW_PADDING)

        # Username field
        self._create_label(form, "Username *")
        self.username_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
        )
        configure_input_style(self.username_entry)
        self.username_entry.pack(anchor="w", pady=(0, 12))

        if self.is_edit_mode:
            self.username_entry.insert(0, self.user.username)
            self.username_entry.configure(state="disabled")

        # Full Name field
        self._create_label(form, "Full Name *")
        self.fullname_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
        )
        configure_input_style(self.fullname_entry)
        self.fullname_entry.pack(anchor="w", pady=(0, 12))

        if self.is_edit_mode:
            self.fullname_entry.insert(0, self.user.full_name)

        # Email field (required)
        self._create_label(form, "Email *")
        self.email_entry = ctk.CTkEntry(
            form,
            width=300,
            height=SPACING.INPUT_HEIGHT,
            font=TYPOGRAPHY.body,
        )
        configure_input_style(self.email_entry)
        self.email_entry.pack(anchor="w", pady=(0, 12))

        if self.is_edit_mode and self.user.email:
            self.email_entry.insert(0, self.user.email)

        # Role dropdown
        self._create_label(form, "Role *")
        self.role_var = ctk.StringVar()
        role_values = [r.display_name for r in UserRole]
        self.role_dropdown = ctk.CTkOptionMenu(
            form,
            values=role_values,
            variable=self.role_var,
            width=200,
            font=TYPOGRAPHY.body,
            dropdown_font=TYPOGRAPHY.body,
            command=self._on_role_changed,
        )
        configure_dropdown_style(self.role_dropdown)
        self.role_dropdown.pack(anchor="w", pady=(0, 12))

        if self.is_edit_mode:
            try:
                role = UserRole(self.user.role)
                self.role_var.set(role.display_name)
            except ValueError:
                self.role_var.set(UserRole.VIEWER.display_name)
        else:
            self.role_var.set(UserRole.VIEWER.display_name)

        # Restrictions section (for EDITOR_RESTRICTED role)
        self.restrictions_frame = ctk.CTkFrame(form, fg_color=COLORS.MUTED, corner_radius=8)
        self._build_restrictions_section()

        # Password fields (only in add mode)
        if not self.is_edit_mode:
            self._create_label(form, "Password *")
            self.password_entry = ctk.CTkEntry(
                form,
                width=300,
                height=SPACING.INPUT_HEIGHT,
                font=TYPOGRAPHY.body,
                show="*",
            )
            configure_input_style(self.password_entry)
            self.password_entry.pack(anchor="w", pady=(0, 12))

            self._create_label(form, "Confirm Password *")
            self.confirm_entry = ctk.CTkEntry(
                form,
                width=300,
                height=SPACING.INPUT_HEIGHT,
                font=TYPOGRAPHY.body,
                show="*",
            )
            configure_input_style(self.confirm_entry)
            self.confirm_entry.pack(anchor="w", pady=(0, 12))

            # Password hint
            hint = ctk.CTkLabel(
                form,
                text="Minimum 8 characters",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            )
            hint.pack(anchor="w", pady=(0, 8))

            # Force password change info
            info_label = ctk.CTkLabel(
                form,
                text="Note: User will be required to change password on first login.",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_SECONDARY,
                wraplength=350,
            )
            info_label.pack(anchor="w", pady=(0, 12))

        # Active checkbox (only in edit mode)
        if self.is_edit_mode:
            self.active_var = ctk.BooleanVar(value=self.user.is_active)
            active_check = ctk.CTkCheckBox(
                form,
                text="Account is active",
                variable=self.active_var,
                font=TYPOGRAPHY.body,
                text_color=COLORS.TEXT_PRIMARY,
            )
            active_check.pack(anchor="w", pady=(0, 12))

        # Button frame
        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(fill="x", padx=SPACING.WINDOW_PADDING, pady=(0, SPACING.WINDOW_PADDING))

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=self._on_cancel,
            width=100,
        )
        configure_button_style(cancel_btn, "secondary")
        cancel_btn.pack(side="right", padx=(8, 0))

        save_btn = ctk.CTkButton(
            btn_frame,
            text="Save" if self.is_edit_mode else "Create User",
            command=self._on_save,
            width=120,
        )
        configure_button_style(save_btn, "primary")
        save_btn.pack(side="right")

    def _create_label(self, parent, text: str) -> None:
        """Create a field label."""
        label = ctk.CTkLabel(
            parent,
            text=text,
            font=TYPOGRAPHY.body,
            text_color=COLORS.TEXT_PRIMARY,
        )
        label.pack(anchor="w", pady=(0, 4))

    def _on_save(self) -> None:
        """Handle save button click."""
        # Validate username
        username = self.username_entry.get().strip()
        if not self.is_edit_mode:
            is_valid, error = validate_username(username)
            if not is_valid:
                InfoDialog.show_error(self, "Invalid Username", error)
                return

            # Check if username exists
            if self.user_service.username_exists(username):
                InfoDialog.show_error(self, "Username Taken", f"Username '{username}' is already in use.")
                return

        # Validate full name
        full_name = self.fullname_entry.get().strip()
        if not full_name or len(full_name) < 2:
            InfoDialog.show_error(self, "Invalid Name", "Please enter a full name (at least 2 characters).")
            return

        # Validate email (required)
        email = self.email_entry.get().strip()
        if not email:
            InfoDialog.show_error(self, "Email Required", "Please enter an email address.")
            return

        is_valid, error = validate_email(email)
        if not is_valid:
            InfoDialog.show_error(self, "Invalid Email", error)
            return

        # Check email uniqueness
        exclude_id = self.user.user_id if self.is_edit_mode else None
        if self.user_service.email_exists(email, exclude_user_id=exclude_id):
            InfoDialog.show_error(self, "Email Taken", f"Email '{email}' is already in use.")
            return

        # Get role
        role_display = self.role_var.get()
        role_value = UserRole.VIEWER.value
        for r in UserRole:
            if r.display_name == role_display:
                role_value = r.value
                break

        # Validate password (add mode only)
        if not self.is_edit_mode:
            password = self.password_entry.get()
            confirm = self.confirm_entry.get()

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
                # Update user
                update_data = UserUpdate(
                    full_name=full_name,
                    email=email,
                    role=role_value,
                    is_active=self.active_var.get(),
                )
                self.user_service.update_user(self.user.user_id, update_data)

                # Update restrictions if EDITOR_RESTRICTED
                if role_value == UserRole.EDITOR_RESTRICTED.value:
                    self.user_service.set_user_restrictions(
                        self.user.user_id,
                        self._get_selected_categories(),
                        self._get_selected_entities(),
                    )
                else:
                    # Clear restrictions if not EDITOR_RESTRICTED
                    self.user_service.clear_user_restrictions(self.user.user_id)

                self.result = True
            else:
                # Create user
                create_data = UserCreate(
                    username=username,
                    password=password,
                    full_name=full_name,
                    email=email,
                    role=role_value,
                )
                created_user = self.user_service.create_user(create_data)

                # Set restrictions if EDITOR_RESTRICTED
                if role_value == UserRole.EDITOR_RESTRICTED.value and created_user:
                    self.user_service.set_user_restrictions(
                        created_user.user_id,
                        self._get_selected_categories(),
                        self._get_selected_entities(),
                    )

                self.result = True

            self.destroy()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to manage users.")
        except ValueError as e:
            InfoDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))

    def _build_restrictions_section(self) -> None:
        """Build the restrictions section for EDITOR_RESTRICTED role."""
        # Header
        header = ctk.CTkLabel(
            self.restrictions_frame,
            text="Access Restrictions",
            font=TYPOGRAPHY.section_heading,
            text_color=COLORS.TEXT_PRIMARY,
        )
        header.pack(anchor="w", padx=12, pady=(12, 4))

        # Description
        desc = ctk.CTkLabel(
            self.restrictions_frame,
            text="User can edit documents matching ANY selected category OR entity.",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_SECONDARY,
            wraplength=420,
        )
        desc.pack(anchor="w", padx=12, pady=(0, 8))

        # Two-column layout for categories and entities
        cols_frame = ctk.CTkFrame(self.restrictions_frame, fg_color="transparent")
        cols_frame.pack(fill="x", padx=12, pady=(0, 12))

        # Categories column
        cat_frame = ctk.CTkFrame(cols_frame, fg_color="transparent")
        cat_frame.pack(side="left", fill="both", expand=True, padx=(0, 8))

        cat_label = ctk.CTkLabel(
            cat_frame,
            text="Allowed Categories:",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_PRIMARY,
        )
        cat_label.pack(anchor="w", pady=(0, 4))

        # Scrollable categories list
        cat_scroll = ctk.CTkScrollableFrame(cat_frame, fg_color=COLORS.CARD, height=100)
        cat_scroll.pack(fill="x")

        categories = self.category_service.get_all_categories()
        for cat in categories:
            var = ctk.BooleanVar(value=False)
            self._category_vars[cat.code] = var
            cb = ctk.CTkCheckBox(
                cat_scroll,
                text=f"{cat.code} - {cat.name}",
                variable=var,
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_PRIMARY,
            )
            cb.pack(anchor="w", pady=2)

        # Entities column
        ent_frame = ctk.CTkFrame(cols_frame, fg_color="transparent")
        ent_frame.pack(side="left", fill="both", expand=True, padx=(8, 0))

        ent_label = ctk.CTkLabel(
            ent_frame,
            text="Allowed Entities:",
            font=TYPOGRAPHY.small,
            text_color=COLORS.TEXT_PRIMARY,
        )
        ent_label.pack(anchor="w", pady=(0, 4))

        # Scrollable entities list
        ent_scroll = ctk.CTkScrollableFrame(ent_frame, fg_color=COLORS.CARD, height=100)
        ent_scroll.pack(fill="x")

        entities = self.entity_service.get_all_entities()
        if entities:
            for entity in entities:
                var = ctk.BooleanVar(value=False)
                self._entity_vars[entity.name] = var
                cb = ctk.CTkCheckBox(
                    ent_scroll,
                    text=entity.name,
                    variable=var,
                    font=TYPOGRAPHY.small,
                    text_color=COLORS.TEXT_PRIMARY,
                )
                cb.pack(anchor="w", pady=2)
        else:
            no_ent = ctk.CTkLabel(
                ent_scroll,
                text="No entities defined yet",
                font=TYPOGRAPHY.small,
                text_color=COLORS.TEXT_MUTED,
            )
            no_ent.pack(anchor="w", pady=4)

        # Load existing restrictions if editing
        if self.is_edit_mode and self.user.role == UserRole.EDITOR_RESTRICTED.value:
            self._load_restrictions()

        # Initially hide if role is not EDITOR_RESTRICTED
        self._on_role_changed(self.role_var.get())

    def _on_role_changed(self, role_display: str) -> None:
        """Handle role dropdown change."""
        # Show/hide restrictions section based on role
        if role_display == UserRole.EDITOR_RESTRICTED.display_name:
            self.restrictions_frame.pack(anchor="w", fill="x", pady=(0, 12))
        else:
            self.restrictions_frame.pack_forget()

    def _load_restrictions(self) -> None:
        """Load existing restrictions for the user."""
        if not self.user:
            return

        restrictions = self.user_service.get_user_restrictions(self.user.user_id)

        # Set category checkboxes
        for code in restrictions["categories"]:
            if code in self._category_vars:
                self._category_vars[code].set(True)

        # Set entity checkboxes
        for name in restrictions["entities"]:
            if name in self._entity_vars:
                self._entity_vars[name].set(True)

    def _get_selected_categories(self) -> List[str]:
        """Get list of selected category codes."""
        return [code for code, var in self._category_vars.items() if var.get()]

    def _get_selected_entities(self) -> List[str]:
        """Get list of selected entity names."""
        return [name for name, var in self._entity_vars.items() if var.get()]
