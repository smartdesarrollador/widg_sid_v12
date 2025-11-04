"""
WorkareaManager - Manipulación del área de trabajo de Windows

Este manager permite reservar espacio en el escritorio de Windows usando
la API SystemParametersInfo con SPI_SETWORKAREA. Esto hace que otras
aplicaciones se ajusten automáticamente al espacio disponible.
"""

import ctypes
from ctypes import wintypes
import logging

logger = logging.getLogger(__name__)


class WorkareaManager:
    """
    Manager para reservar espacio en el escritorio de Windows

    Usa SystemParametersInfo con SPI_SETWORKAREA para modificar
    el área disponible para otras aplicaciones.
    """

    # Windows API Constants
    SPI_GETWORKAREA = 0x0030
    SPI_SETWORKAREA = 0x002F
    SPIF_UPDATEINIFILE = 0x01
    SPIF_SENDCHANGE = 0x02

    def __init__(self):
        """Inicializar WorkareaManager"""
        self.original_workarea = None
        self.is_space_reserved = False
        self.reserved_width = 0
        self.reserved_side = None  # 'left' o 'right'

        # Guardar área original
        self.save_original_workarea()
        logger.info("WorkareaManager initialized")

    def save_original_workarea(self):
        """Guardar el área de trabajo original"""
        try:
            workarea = wintypes.RECT()

            result = ctypes.windll.user32.SystemParametersInfoW(
                self.SPI_GETWORKAREA,
                0,
                ctypes.byref(workarea),
                0
            )

            if result:
                self.original_workarea = {
                    'left': workarea.left,
                    'top': workarea.top,
                    'right': workarea.right,
                    'bottom': workarea.bottom
                }
                logger.info(f"Original workarea saved: {self.original_workarea}")
            else:
                logger.error("Failed to get original workarea")
                self.original_workarea = None

        except Exception as e:
            logger.error(f"Error saving original workarea: {e}")
            self.original_workarea = None

    def reserve_space_left(self, width):
        """
        Reservar espacio en el lado izquierdo de la pantalla

        Args:
            width: Ancho en píxeles a reservar

        Returns:
            bool: True si se reservó correctamente
        """
        if not self.original_workarea:
            logger.error("Original workarea not available")
            return False

        # Si ya hay espacio reservado, restaurar primero
        if self.is_space_reserved:
            self.restore_workarea()

        try:
            workarea = wintypes.RECT()
            workarea.left = self.original_workarea['left'] + width
            workarea.top = self.original_workarea['top']
            workarea.right = self.original_workarea['right']
            workarea.bottom = self.original_workarea['bottom']

            result = ctypes.windll.user32.SystemParametersInfoW(
                self.SPI_SETWORKAREA,
                0,
                ctypes.byref(workarea),
                self.SPIF_UPDATEINIFILE | self.SPIF_SENDCHANGE
            )

            if result:
                self.is_space_reserved = True
                self.reserved_width = width
                self.reserved_side = 'left'
                logger.info(f"Reserved {width}px on left side")
                return True
            else:
                logger.error("Failed to reserve space on left")
                return False

        except Exception as e:
            logger.error(f"Error reserving space on left: {e}")
            return False

    def reserve_space_right(self, width):
        """
        Reservar espacio en el lado derecho de la pantalla

        Args:
            width: Ancho en píxeles a reservar

        Returns:
            bool: True si se reservó correctamente
        """
        if not self.original_workarea:
            logger.error("Original workarea not available")
            return False

        # Si ya hay espacio reservado, restaurar primero
        if self.is_space_reserved:
            self.restore_workarea()

        try:
            workarea = wintypes.RECT()
            workarea.left = self.original_workarea['left']
            workarea.top = self.original_workarea['top']
            workarea.right = self.original_workarea['right'] - width
            workarea.bottom = self.original_workarea['bottom']

            result = ctypes.windll.user32.SystemParametersInfoW(
                self.SPI_SETWORKAREA,
                0,
                ctypes.byref(workarea),
                self.SPIF_UPDATEINIFILE | self.SPIF_SENDCHANGE
            )

            if result:
                self.is_space_reserved = True
                self.reserved_width = width
                self.reserved_side = 'right'
                logger.info(f"Reserved {width}px on right side")
                return True
            else:
                logger.error("Failed to reserve space on right")
                return False

        except Exception as e:
            logger.error(f"Error reserving space on right: {e}")
            return False

    def restore_workarea(self):
        """Restaurar el área de trabajo original"""
        if not self.original_workarea:
            logger.error("No original workarea to restore")
            return False

        try:
            workarea = wintypes.RECT()
            workarea.left = self.original_workarea['left']
            workarea.top = self.original_workarea['top']
            workarea.right = self.original_workarea['right']
            workarea.bottom = self.original_workarea['bottom']

            result = ctypes.windll.user32.SystemParametersInfoW(
                self.SPI_SETWORKAREA,
                0,
                ctypes.byref(workarea),
                self.SPIF_UPDATEINIFILE | self.SPIF_SENDCHANGE
            )

            if result:
                self.is_space_reserved = False
                self.reserved_width = 0
                self.reserved_side = None
                logger.info("Workarea restored to original")
                return True
            else:
                logger.error("Failed to restore workarea")
                return False

        except Exception as e:
            logger.error(f"Error restoring workarea: {e}")
            return False

    def get_status(self):
        """
        Obtener estado actual del workarea manager

        Returns:
            dict: Estado actual con información de reserva
        """
        return {
            'is_reserved': self.is_space_reserved,
            'width': self.reserved_width,
            'side': self.reserved_side,
            'original': self.original_workarea
        }

    def __del__(self):
        """Restaurar al destruir el objeto"""
        if self.is_space_reserved:
            logger.info("WorkareaManager destructor: restoring workarea")
            self.restore_workarea()
