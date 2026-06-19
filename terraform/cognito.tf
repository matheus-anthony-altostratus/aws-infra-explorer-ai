resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"

  # Solo admins pueden crear usuarios (no auto-registro público)
  admin_create_user_config {
    allow_admin_create_user_only = true
    invite_message_template {
      email_subject = "Bienvenido a Infra Explorer AI — Altostratus"
      email_message = "Hola,\n\nTu cuenta ha sido creada en Infra Explorer AI.\n\nEmail: {username}\nContraseña temporal: {####}\n\nAccede en: https://d2y8h0jbecvclg.cloudfront.net\nDeberás cambiar tu contraseña en el primer inicio de sesión.\n\nAltostratus CMC Team"
      sms_message   = "{username} — Tu contraseña temporal para Infra Explorer AI es: {####}"
    }
  }

  # Verificación por email
  auto_verified_attributes = ["email"]
  username_attributes      = ["email"]

  # Política de contraseñas
  password_policy {
    minimum_length                   = 8
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = false
    temporary_password_validity_days = 7
  }

  # Schema de atributos
  schema {
    name                = "email"
    attribute_data_type = "String"
    required            = true
    mutable             = true
  }

  # Lambda trigger: bloquea emails que no sean @altostratus.es
  lambda_config {
    pre_sign_up = aws_lambda_function.cognito_presignup.arn
  }

  # Tokens
  user_pool_add_ons {
    advanced_security_mode = "OFF"
  }
}

resource "aws_cognito_user_pool_client" "web" {
  name         = "${var.project_name}-web-client"
  user_pool_id = aws_cognito_user_pool.main.id

  # Sin secret (SPA pública con PKCE)
  generate_secret = false

  # Flujo OAuth2 con PKCE
  allowed_oauth_flows                  = ["code"]
  allowed_oauth_scopes                 = ["email", "openid", "profile"]
  allowed_oauth_flows_user_pool_client = true
  supported_identity_providers         = ["COGNITO"]

  # URLs de callback (CloudFront)
  callback_urls = ["https://d2y8h0jbecvclg.cloudfront.net/callback"]
  logout_urls   = ["https://d2y8h0jbecvclg.cloudfront.net"]

  # Tokens
  access_token_validity  = 60 # minutos
  id_token_validity      = 60 # minutos
  refresh_token_validity = 30 # días

  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }

  explicit_auth_flows = [
    "ALLOW_USER_SRP_AUTH",
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH",
  ]
}

# Dominio para la Hosted UI
resource "aws_cognito_user_pool_domain" "main" {
  domain       = "${var.project_name}-${var.environment}"
  user_pool_id = aws_cognito_user_pool.main.id
}
