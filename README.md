# Chess Game♟️

[![Python Version](https://img.shields.io/badge/python-3.x-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) 

A multi-client chess application built with Python and Pygame. This project serves as a practical demonstration of computer network programming principles, focusing on client-server communication for real-time gameplay between two players over a network.

<!-- Consider adding a screenshot or GIF of the gameplay here! -->
<!-- ![Gameplay Screenshot](link/to/your/screenshot.png) -->

## ✨ Features

*   **Two-Player Network Gameplay:** Play chess against another person on a different machine.
*   **Client-Server Architecture:** Centralized server manages game state and client connections.
*   **Graphical User Interface:** Interactive chessboard powered by Pygame.
*   **Real-time Move Synchronization:** Moves are instantly reflected on both players' screens.

## 🚀 Motivation

The primary goal was to apply theoretical knowledge of network sockets, client-server interaction, and basic data exchange protocols in a tangible and interactive application.

## 🛠️ Technologies Used

*   **Python 3.x:** Core programming language.
*   **Pygame:** Library for creating the graphical interface and handling user input.
*   **Python `socket` module:** For implementing the underlying network communication.

## ⚙️ Setup and Installation

Follow these steps to get the application running locally:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/hackerpranavpandey/Computer-Networks-Project.git
    cd Computer-Networks-Project
    ```

2.  **Create a Virtual Environment (Recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install Dependencies:**
    Make sure you have `pip` installed. Run the following command in the project directory:
    ```bash
    pip install -r requirements.txt
    ```

## ▶️ How to Run

1.  **Start the Server:**
    Open a terminal in the project directory and run:
    ```bash
    python server.py
    ```
    The server will start listening for incoming client connections. By default, it usually listens on `localhost` (127.0.0.1) on a specific port (you might need to specify or check the code for the exact port).

2.  **Start the First Client:**
    Open a *new* terminal, navigate to the project directory (and activate the virtual environment if you created one):
    ```bash
    python client.py
    ```
    This will launch the Pygame window for the first player and attempt to connect to the server.

3.  **Start the Second Client:**
    Open *another* new terminal, navigate to the project directory (and activate the virtual environment):
    ```bash
    python client.py
    ```
    This launches the second player's client. Once both clients connect to the server, the game should begin!

*(Note: If clients are on different machines, ensure the `client.py` code correctly points to the server's IP address, not just `localhost`, and that firewalls allow the connection.)*

## 🤝 Contributors

*   Parikshit Gehlaut
*   Pranav Kumar Pandey
*   Amit Singh
*   Mahesh Krishnam
*   Harsh Jain

## 📜 License

This project is licensed under the MIT License - see the `LICENSE` file for details. *(You should **add a LICENSE file** to your repository - the MIT license is a common permissive choice)*.

## 🙏 Contributing

Contributions, issues, and feature requests are welcome. Feel free to check [issues page](https://github.com/hackerpranavpandey/Computer-Networks-Project/issues) if you want to contribute. *(Adjust this section based on whether you are open to contributions)*.
