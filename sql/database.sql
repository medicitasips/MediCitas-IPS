-- =============================================================
-- BASE DE DATOS: railway  (versión 1 – roles + catálogos)
-- Sistema de Gestión de Citas Médicas
-- Programa ADSO19 – SENA
-- =============================================================

CREATE DATABASE IF NOT EXISTS railway
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_spanish_ci;

USE railway;

-- =============================================================
-- CATÁLOGO: eps
-- Listado oficial de EPS disponibles en el sistema
-- =============================================================
CREATE TABLE IF NOT EXISTS eps (
    id_eps   INT          NOT NULL AUTO_INCREMENT,
    nombre   VARCHAR(120) NOT NULL,
    activa   TINYINT(1)   NOT NULL DEFAULT 1,
    CONSTRAINT pk_eps    PRIMARY KEY (id_eps),
    CONSTRAINT uq_eps    UNIQUE (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================
-- CATÁLOGO: especialidades  (tipos de cita)
-- =============================================================
CREATE TABLE IF NOT EXISTS especialidades (
    id_especialidad INT         NOT NULL AUTO_INCREMENT,
    nombre          VARCHAR(80) NOT NULL,
    duracion_min    INT         NOT NULL DEFAULT 30
        COMMENT 'Duración estándar de la cita en minutos',
    activa          TINYINT(1)  NOT NULL DEFAULT 1,
    CONSTRAINT pk_especialidad PRIMARY KEY (id_especialidad),
    CONSTRAINT uq_especialidad UNIQUE (nombre)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- =============================================================
-- TABLA: usuarios
-- Gestiona el acceso al sistema con rol asignado
-- =============================================================
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario     INT          NOT NULL AUTO_INCREMENT,
    username       VARCHAR(60)  NOT NULL,
    password_hash  VARCHAR(255) NOT NULL,
    rol            ENUM('admin','medico','paciente') NOT NULL DEFAULT 'paciente',
    activo         TINYINT(1)   NOT NULL DEFAULT 1,
    fecha_registro DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_usuario  PRIMARY KEY (id_usuario),
    CONSTRAINT uq_username UNIQUE (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_usuario_rol ON usuarios (rol);

-- =============================================================
-- TABLA: medicos
-- Información del médico, vinculado a un usuario del sistema
-- =============================================================
CREATE TABLE IF NOT EXISTS medicos (
    id_medico       INT          NOT NULL AUTO_INCREMENT,
    id_usuario      INT          NOT NULL,
    documento       VARCHAR(15)  NOT NULL,
    nombre          VARCHAR(80)  NOT NULL,
    apellido        VARCHAR(80)  NOT NULL,
    telefono        VARCHAR(20)  NOT NULL,
    correo          VARCHAR(100) NOT NULL,
    id_especialidad INT          NOT NULL,
    activo          TINYINT(1)   NOT NULL DEFAULT 1,
    CONSTRAINT pk_medico        PRIMARY KEY (id_medico),
    CONSTRAINT uq_medico_doc    UNIQUE (documento),
    CONSTRAINT uq_medico_correo UNIQUE (correo),
    CONSTRAINT uq_medico_usr    UNIQUE (id_usuario),
    CONSTRAINT fk_medico_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_medico_especialidad
        FOREIGN KEY (id_especialidad)
        REFERENCES especialidades (id_especialidad)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_medico_especialidad ON medicos (id_especialidad);

-- =============================================================
-- TABLA: pacientes
-- =============================================================
CREATE TABLE IF NOT EXISTS pacientes (
    id_paciente    INT          NOT NULL AUTO_INCREMENT,
    id_usuario     INT          NOT NULL,
    documento      VARCHAR(15)  NOT NULL,
    nombre         VARCHAR(80)  NOT NULL,
    apellido       VARCHAR(80)  NOT NULL,
    telefono       VARCHAR(20)  NOT NULL,
    correo         VARCHAR(100) NOT NULL,
    id_eps         INT          NOT NULL,
    fecha_registro DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_paciente     PRIMARY KEY (id_paciente),
    CONSTRAINT uq_pac_doc      UNIQUE (documento),
    CONSTRAINT uq_pac_correo   UNIQUE (correo),
    CONSTRAINT uq_pac_usuario  UNIQUE (id_usuario),
    CONSTRAINT fk_pac_usuario
        FOREIGN KEY (id_usuario)
        REFERENCES usuarios (id_usuario)
        ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_pac_eps
        FOREIGN KEY (id_eps)
        REFERENCES eps (id_eps)
        ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_paciente_documento ON pacientes (documento);

-- =============================================================
-- TABLA: citas
-- La validación de cruce se hace a nivel de aplicación
-- con la consulta verify_cruce (ver cita_model.py)
-- =============================================================
CREATE TABLE IF NOT EXISTS citas (
    id_cita         INT      NOT NULL AUTO_INCREMENT,
    id_paciente     INT      NOT NULL,
    id_medico       INT      NOT NULL,
    id_especialidad INT      NOT NULL,
    fecha           DATE     NOT NULL,
    hora_inicio     TIME     NOT NULL,
    hora_fin        TIME     NOT NULL
        COMMENT 'Calculado: hora_inicio + duracion_min de la especialidad',
    id_eps          INT      NOT NULL,
    estado          ENUM('Activa','Cancelada','Completada') NOT NULL DEFAULT 'Activa',
    motivo          VARCHAR(255) NULL,
    fecha_registro  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_cita        PRIMARY KEY (id_cita),
    CONSTRAINT fk_cita_pac    FOREIGN KEY (id_paciente)     REFERENCES pacientes     (id_paciente)     ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_cita_med    FOREIGN KEY (id_medico)       REFERENCES medicos       (id_medico)       ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_cita_esp    FOREIGN KEY (id_especialidad) REFERENCES especialidades(id_especialidad) ON UPDATE CASCADE ON DELETE RESTRICT,
    CONSTRAINT fk_cita_eps    FOREIGN KEY (id_eps)          REFERENCES eps           (id_eps)          ON UPDATE CASCADE ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_cita_medico_fecha ON citas (id_medico, fecha);
CREATE INDEX idx_cita_pac_fecha    ON citas (id_paciente, fecha);

-- =============================================================
-- TABLA: notas_consulta
-- Observaciones clínicas que el médico registra al completar
-- una cita. Relación 1-a-1 con citas.
-- =============================================================
CREATE TABLE IF NOT EXISTS notas_consulta (
    id_nota             INT           NOT NULL AUTO_INCREMENT,
    id_cita             INT           NOT NULL,
    diagnostico         TEXT          NOT NULL
        COMMENT 'Impresión diagnóstica o diagnóstico definitivo',
    tratamiento         TEXT          NULL
        COMMENT 'Medicamentos, procedimientos o indicaciones indicadas',
    proxima_cita        VARCHAR(255)  NULL
        COMMENT 'Recomendación de seguimiento (ej: en 3 semanas)',
    observaciones       TEXT          NULL
        COMMENT 'Notas adicionales del médico',
    fecha_registro      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_nota       PRIMARY KEY (id_nota),
    CONSTRAINT uq_nota_cita  UNIQUE (id_cita),
    CONSTRAINT fk_nota_cita
        FOREIGN KEY (id_cita)
        REFERENCES citas (id_cita)
        ON UPDATE CASCADE ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE INDEX idx_nota_cita ON notas_consulta (id_cita);

-- =============================================================
-- DATOS INICIALES – Catálogos
-- =============================================================
INSERT INTO eps (nombre) VALUES
  ('Sura'), ('Compensar'), ('Sanitas'), ('Colmédica'),
  ('Famisanar'), ('Nueva EPS'), ('Coomeva'), ('Salud Total');

INSERT INTO especialidades (nombre, duracion_min) VALUES
  ('Medicina General',    20),
  ('Odontología',         30),
  ('Pediatría',           30),
  ('Ginecología',         30),
  ('Cardiología',         40),
  ('Dermatología',        30),
  ('Oftalmología',        30),
  ('Ortopedia',           40),
  ('Neurología',          40),
  ('Psicología',          50),
  ('Nutrición y Dietética', 40),
  ('Medicina Interna',    30);

-- =============================================================
-- USUARIOS DE PRUEBA
-- Contraseñas en texto plano aquí solo para referencia;
-- el sistema almacenará el hash generado por Werkzeug.
--
--   admin    / Admin2025*

INSERT INTO usuarios (username, password_hash, rol)
VALUES ('admin', 'scrypt:32768:8:1$rEEcyklYcuCllGUm$6701996c2f7d185285ff9dab9cf8ad0d57c54ecf75f3c067272f7b50232e53b59338cd7c0b867fa7340706a918635d6dc9a431db6d2215abd597cbe46966225d', 'admin');
-- =============================================================

-- Se insertan desde Python al arrancar (ver app.py seed_db)
-- para garantizar que el hash sea correcto.
-- Si quieres insertarlos manualmente, usa los hashes
-- generados con: python -c "from werkzeug.security import generate_password_hash; print(generate_password_hash('Admin2025*'))"

-- =============================================================
-- CONSULTA JOIN DE REFERENCIA – cita completa
-- =============================================================
-- SELECT
--     p.nombre AS pac_nombre, p.apellido AS pac_apellido,
--     m.nombre AS med_nombre, m.apellido AS med_apellido,
--     e.nombre AS especialidad,
--     c.fecha, c.hora_inicio, c.hora_fin,
--     eps.nombre AS eps_nombre,
--     c.estado, c.motivo
-- FROM citas c
-- INNER JOIN pacientes     p   ON c.id_paciente     = p.id_paciente
-- INNER JOIN medicos       m   ON c.id_medico       = m.id_medico
-- INNER JOIN especialidades e  ON c.id_especialidad = e.id_especialidad
-- INNER JOIN eps               ON c.id_eps          = eps.id_eps
-- WHERE p.documento = %s
-- ORDER BY c.fecha, c.hora_inicio;
