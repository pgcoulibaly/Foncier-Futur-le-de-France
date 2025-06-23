import subprocess
import sys
import os
import time
import signal
import platform
from pathlib import Path

# Définir la variable d'environnement pour désactiver __pycache__
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"


class AppManager:
    def __init__(self):
        self.api_process = None
        self.streamlit_process = None

    def start_api(self):
        """Démarre l'API FastAPI avec rechargement automatique"""
        print("Démarrage de l'API FastAPI avec auto-reload...")

        # Commande avec rechargement automatique optimisé
        cmd = [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.app:app",
            "--reload",  # Rechargement automatique
            "--reload-dir",
            "backend",  # Surveiller seulement le dossier backend
            "--reload-dir",
            "core",  # Surveiller aussi le dossier core
            "--log-level",
            "info",  # Logs détaillés
            "--host",
            "0.0.0.0",  # Accessible de partout
            "--port",
            "8000",  # Port fixe
        ]

        self.api_process = subprocess.Popen(cmd)
        return self.api_process

    def start_streamlit(self):
        """Démarre Streamlit avec rechargement automatique"""
        print("Démarrage de Streamlit avec auto-reload...")

        # Streamlit a déjà le rechargement automatique intégré
        cmd = [
            sys.executable,
            "-m",
            "streamlit",
            "run",
            "./frontend/app_front.py",
            "--server.runOnSave",
            "true",  # Rechargement auto
            "--server.fileWatcherType",
            "auto",  # Surveillance optimisée
            "--browser.gatherUsageStats",
            "false",  # Pas de stats
        ]

        self.streamlit_process = subprocess.Popen(cmd)
        return self.streamlit_process

    def stop_all(self):
        """Arrête proprement tous les processus"""
        print("Arrêt des applications...")

        processes = [self.api_process, self.streamlit_process]

        for process in processes:
            if process and process.poll() is None:
                try:
                    # Arrêt propre
                    if platform.system() == "Windows":
                        process.terminate()
                    else:
                        process.send_signal(signal.SIGTERM)

                    # Attendre un peu
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        # Forcer l'arrêt si nécessaire
                        process.kill()

                except Exception as e:
                    print(f"Erreur lors de l'arrêt: {e}")

        print("Applications arrêtées proprement")


def main():
    """Fonction principale avec gestion des erreurs"""
    manager = AppManager()

    try:
        # Démarrer l'API
        manager.start_api()

        # Attendre un peu que l'API démarre
        time.sleep(3)

        # Démarrer Streamlit
        manager.start_streamlit()

        print("\n" + "=" * 50)
        print("APPLICATIONS DÉMARRÉES AVEC AUTO-RELOAD")
        print("=" * 50)
        print("API FastAPI: http://localhost:8000")
        print("Streamlit: http://localhost:8501")
        print("Modifications détectées automatiquement")
        print("Ctrl+C pour arrêter")
        print("=" * 50 + "\n")

        # Attendre que l'utilisateur interrompe
        try:
            while True:
                # Vérifier que les processus tournent encore
                if manager.api_process and manager.api_process.poll() is not None:
                    print("L'API s'est arrêtée inopinément")
                    break
                if (
                    manager.streamlit_process
                    and manager.streamlit_process.poll() is not None
                ):
                    print("Streamlit s'est arrêté inopinément")
                    break

                time.sleep(1)

        except KeyboardInterrupt:
            print("\nArrêt demandé par l'utilisateur")

    except Exception as e:
        print(f"Erreur: {e}")

    finally:
        manager.stop_all()


if __name__ == "__main__":
    main()
