STYLE_SHEET = """
QWidget {
    background-color: #FFFFFF;
    color: #202020;
    font-family: "Calibri";
    font-size: 15px;
}

QLabel#page_title {
    font-size: 28px;
    font-weight: 700;
    padding: 8px;
}

QLabel#section_title {
    font-size: 19px;
    font-weight: 700;
}

QWidget#header {
    background-color: #D2F6E7;
    border-bottom: 1px solid #70B2AF;
}

QWidget#header QLabel {
    background: transparent;
}

QPushButton {
    background-color: #70B2AF;
    border: 1px solid #579793;
    border-radius: 6px;
    padding: 8px 14px;
    min-height: 22px;
}

QPushButton:hover {
    background-color: #82C4C1;
}

QPushButton:disabled {
    background-color: #D7E2E1;
    color: #707070;
}

QPushButton#secondary_button {
    background-color: #D2F6E7;
}

QLineEdit, QComboBox, QSpinBox, QDateEdit {
    background-color: #FFFFFF;
    border: 1px solid #70B2AF;
    border-radius: 5px;
    padding: 7px;
    min-height: 24px;
}

QScrollArea {
    border: none;
}

QFrame#product_card {
    border: 1px solid #70B2AF;
    border-radius: 8px;
    background-color: #FFFFFF;
}

QFrame#product_card[low_stock="true"] {
    background-color: #ff8080;
}

QFrame#product_card QLabel {
    background: transparent;
}

QLabel#product_name {
    font-size: 18px;
    font-weight: 700;
}

QLabel#price {
    font-size: 18px;
    font-weight: 700;
}

QTableWidget {
    background-color: #FFFFFF;
    border: 1px solid #70B2AF;
    gridline-color: #C7DEDC;
    selection-background-color: #D2F6E7;
    selection-color: #202020;
}

QHeaderView::section {
    background-color: #D2F6E7;
    border: 1px solid #B9D7D5;
    padding: 7px;
    font-weight: 700;
}

QMessageBox QPushButton {
    min-width: 90px;
}
"""
