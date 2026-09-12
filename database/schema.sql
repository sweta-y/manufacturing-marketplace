CREATE TABLE users (
    user_id         SERIAL PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('customer','manufacturer','admin')),
    full_name       VARCHAR(150) NOT NULL,
    phone           VARCHAR(20),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE customer_profiles (
    customer_profile_id SERIAL PRIMARY KEY,
    user_id         INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    company_name    VARCHAR(150),
    address         TEXT,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE manufacturer_profiles (
    manufacturer_profile_id SERIAL PRIMARY KEY,
    user_id         INT UNIQUE REFERENCES users(user_id) ON DELETE CASCADE,
    business_name   VARCHAR(150) NOT NULL,
    address         TEXT,
    approval_status VARCHAR(20) DEFAULT 'pending' CHECK (approval_status IN ('pending','approved','rejected')),
    rejection_reason TEXT,
    approved_at     TIMESTAMP,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(user_id) ON DELETE CASCADE,
    message         TEXT NOT NULL,
    created_at      TIMESTAMP DEFAULT NOW(),
    is_read         BOOLEAN DEFAULT FALSE
);

CREATE TABLE manufacturing_processes (
    process_id      SERIAL PRIMARY KEY,
    name            VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE materials (
    material_id     SERIAL PRIMARY KEY,
    name            VARCHAR(80) UNIQUE NOT NULL,
    process_id      INT REFERENCES manufacturing_processes(process_id)
);

CREATE TABLE machines (
    machine_id      SERIAL PRIMARY KEY,
    manufacturer_profile_id INT REFERENCES manufacturer_profiles(manufacturer_profile_id) ON DELETE CASCADE,
    machine_name    VARCHAR(120) NOT NULL,
    process_id      INT REFERENCES manufacturing_processes(process_id),
    max_dimensions  VARCHAR(100),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE machine_capabilities (
    capability_id   SERIAL PRIMARY KEY,
    machine_id      INT REFERENCES machines(machine_id) ON DELETE CASCADE,
    material_id     INT REFERENCES materials(material_id),
    max_quantity    INT DEFAULT 1000,
    UNIQUE(machine_id, material_id)
);

CREATE TABLE uploaded_files (
    file_id         SERIAL PRIMARY KEY,
    user_id         INT REFERENCES users(user_id),
    filename        VARCHAR(255) NOT NULL,
    file_type       VARCHAR(10) NOT NULL,
    file_size_kb    INT,
    storage_path    VARCHAR(500) NOT NULL,
    uploaded_at     TIMESTAMP DEFAULT NOW()
);

CREATE TABLE manufacturing_requests (
    request_id      SERIAL PRIMARY KEY,
    customer_profile_id INT REFERENCES customer_profiles(customer_profile_id),
    file_id         INT REFERENCES uploaded_files(file_id),
    process_id      INT REFERENCES manufacturing_processes(process_id),
    material_id     INT REFERENCES materials(material_id),
    quantity        INT NOT NULL CHECK (quantity > 0),
    surface_finish  VARCHAR(50),
    notes           TEXT,
    estimated_cost  NUMERIC(10,2),
    estimated_days  INT,
    status          VARCHAR(30) DEFAULT 'draft',
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE request_requirements (
    requirement_id  SERIAL PRIMARY KEY,
    request_id      INT REFERENCES manufacturing_requests(request_id) ON DELETE CASCADE,
    label           VARCHAR(100),
    detail          TEXT
);

CREATE TABLE orders (
    order_id        SERIAL PRIMARY KEY,
    request_id      INT REFERENCES manufacturing_requests(request_id),
    manufacturer_profile_id INT REFERENCES manufacturer_profiles(manufacturer_profile_id),
    machine_id      INT REFERENCES machines(machine_id),
    status          VARCHAR(30) NOT NULL DEFAULT 'Request Submitted'
        CHECK (status IN ('Request Submitted','Manufacturer Selected','Accepted',
                           'Manufacturing','Quality Check','Completed','Cancelled')),
    final_cost      NUMERIC(10,2),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE order_status_history (
    history_id      SERIAL PRIMARY KEY,
    order_id        INT REFERENCES orders(order_id) ON DELETE CASCADE,
    status          VARCHAR(30) NOT NULL,
    changed_by      INT REFERENCES users(user_id),
    changed_at      TIMESTAMP DEFAULT NOW(),
    remarks         TEXT
);

CREATE INDEX idx_requests_customer ON manufacturing_requests(customer_profile_id);
CREATE INDEX idx_requests_status ON manufacturing_requests(status);
CREATE INDEX idx_orders_manufacturer ON orders(manufacturer_profile_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_machines_manufacturer ON machines(manufacturer_profile_id);
CREATE INDEX idx_capabilities_machine ON machine_capabilities(machine_id);
CREATE INDEX idx_history_order ON order_status_history(order_id);
