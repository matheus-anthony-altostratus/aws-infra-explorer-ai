resource "aws_cognito_user_pool" "main" {
  name = "${var.project_name}-users"

  # Solo admins pueden crear usuarios (no auto-registro público)
  admin_create_user_config {
    allow_admin_create_user_only = true
    invite_message_template {
      email_subject = "Tu acceso a Infra Explorer AI — crea tu contraseña"
      email_message = <<-EOT
        <p>Hola,</p>

        <p>Se te ha dado acceso a <strong>Infra Explorer AI</strong>, la herramienta interna de Altostratus.</p>

        <p><strong>Tu contraseña definitiva la creas tú en el primer inicio de sesión.</strong>
        Para ello necesitas esta contraseña temporal de un solo uso:</p>

        <table cellpadding="10" style="border:1px solid #d0d7e2; border-radius:8px; background:#f5f8ff;">
          <tr><td>Usuario:</td><td><strong>{username}</strong></td></tr>
          <tr><td>Contraseña temporal:</td><td><strong style="font-size:16px;">{####}</strong></td></tr>
        </table>

        <p><strong>Pasos a seguir:</strong></p>
        <ol>
          <li>Entra en <a href="https://d2y8h0jbecvclg.cloudfront.net">https://d2y8h0jbecvclg.cloudfront.net</a></li>
          <li>Inicia sesión con tu correo y la <em>contraseña temporal</em> de arriba.</li>
          <li>La aplicación te pedirá inmediatamente que <strong>establezcas tu contraseña definitiva</strong>. Esa será la que uses a partir de ese momento.</li>
        </ol>

        <p>La contraseña definitiva debe tener mínimo 8 caracteres, con al menos una mayúscula, una minúscula y un número.</p>

        <p><strong>Importante:</strong> la contraseña temporal caduca en 7 días. Si expira, pide a un compañero del equipo CMC-AWS que pulse "Reset" sobre tu usuario para recibir un correo nuevo.</p>

        <p>Altostratus CMC Team</p>
      EOT
      sms_message   = "Infra Explorer AI — usuario {username}, contraseña temporal {####}. Al entrar tendrás que crear tu contraseña definitiva."
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
