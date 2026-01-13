"""
PolicyHub User Dialog

Dialog for adding and editing users.
"""

from typing import Optional

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
        self.user = user
        self.is_edit_mode = user is not None

        title = "Edit User" if self.is_edit_mode else "Add User"
        height = 400 if self.is_edit_mode else 480

        super().__init__(parent, title, width=450, height=height)
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
                self.user_service.create_user(create_data)
                self.result = True

            self.destroy()

        except PermissionError:
            InfoDialog.show_error(self, "Permission Denied", "You do not have permission to manage users.")
        except ValueError as e:
            InfoDialog.show_error(self, "Validation Error", str(e))
        except Exception as e:
            InfoDialog.show_error(self, "Error", str(e))
