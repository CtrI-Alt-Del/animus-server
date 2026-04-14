RESET_PASSWORD_EMAIL_TEMPLATE = """<!doctype html>
<html lang="pt-BR" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Redefinição de senha</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f3f4f6;">
    <div
      style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all;"
    >
      Recupere o acesso à sua conta no Animus.
    </div>

    <table
      role="presentation"
      cellpadding="0"
      cellspacing="0"
      border="0"
      width="100%"
      style="background-color:#f3f4f6; margin:0; padding:0; width:100%;"
    >
      <tr>
        <td align="center" style="padding:24px 12px;">
          <table
            role="presentation"
            cellpadding="0"
            cellspacing="0"
            border="0"
            width="600"
            style="width:100%; max-width:600px; background-color:#ffffff; border-collapse:collapse;"
          >
            <tr>
              <td
                align="center"
                style="background-color:#fbe26d; padding:18px 24px; font-family:Georgia, 'Times New Roman', serif; font-size:28px; font-weight:600; color:#0b0b0e; line-height:1.2;"
              >
                Animus
              </td>
            </tr>

            <tr>
              <td style="padding:40px 40px 24px 40px; font-family:Arial, Helvetica, sans-serif; color:#1a1a1e;">
                <h1
                  style="margin:0 0 24px 0; font-size:32px; line-height:1.2; font-weight:700; color:#1a1a1e;"
                >
                  Redefinição de senha
                </h1>

                <p
                  style="margin:0 0 20px 0; font-size:16px; line-height:1.6; color:#1a1a1e;"
                >
                  Olá,
                </p>

                <p
                  style="margin:0 0 28px 0; font-size:14px; line-height:1.7; color:#4a4a50;"
                >
                  Recebemos uma solicitação para redefinir a senha da sua conta no Animus. Use o código numérico abaixo para continuar o processo no aplicativo. Este código é válido por tempo limitado.
                </p>

                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                >
                  <tr>
                    <td align="center" style="padding:10px 0 30px 0;">
                      <div
                        style="display:inline-block; background-color:#1a1a1e; color:#ffffff; font-family:Arial, Helvetica, sans-serif; font-size:32px; font-weight:700; letter-spacing:8px; text-decoration:none; padding:16px 32px; border-radius:8px;"
                      >
                        {{OTP_CODE}}
                      </div>
                    </td>
                  </tr>
                </table>

                <p
                  style="margin:0 0 24px 0; font-size:12px; line-height:1.6; text-align:center; color:#8e8e93;"
                >
                  Se o código expirar, você precisará solicitar uma nova redefinição no aplicativo.
                </p>

                <hr
                  style="border:0; border-top:1px solid #e5e5e5; margin:0 0 20px 0;"
                />

                <p
                  style="margin:0 0 10px 0; font-size:12px; line-height:1.6; text-align:center; color:#8e8e93;"
                >
                  Se você não solicitou a redefinição de senha, ignore este e-mail com segurança. Sua conta continua protegida e sua senha atual não será alterada.
                </p>

                <p
                  style="margin:0; font-size:11px; line-height:1.5; text-align:center; color:#8e8e93;"
                >
                  Animus &copy; 2026
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""
