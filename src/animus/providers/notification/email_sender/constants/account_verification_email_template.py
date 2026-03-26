ACCOUNT_VERIFICATION_EMAIL_TEMPLATE = """<!doctype html>
<html lang="pt-BR" xmlns="http://www.w3.org/1999/xhtml">
  <head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Confirme seu e-mail</title>
  </head>
  <body style="margin:0; padding:0; background-color:#f3f4f6;">
    <div
      style="display:none; max-height:0; overflow:hidden; opacity:0; mso-hide:all;"
    >
      Use o codigo de verificação para confirmar seu e-mail e ativar sua conta no Animus.
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
                  Confirme seu e-mail
                </h1>

                <p
                  style="margin:0 0 20px 0; font-size:16px; line-height:1.6; color:#1a1a1e;"
                >
                  Ola,
                </p>

                <p
                  style="margin:0 0 28px 0; font-size:14px; line-height:1.7; color:#4a4a50;"
                >
                  Use o codigo OTP abaixo para confirmar seu e-mail e ativar sua
                  conta no Animus. Este codigo e valido por 1 hora.
                </p>

                <table
                  role="presentation"
                  cellpadding="0"
                  cellspacing="0"
                  border="0"
                  width="100%"
                  style="border-collapse:separate; background-color:#fff9db; border:1px solid #fbe26d55; border-radius:12px;"
                >
                  <tr>
                    <td align="center" style="padding:18px 24px 8px 24px;">
                      <p
                        style="margin:0; font-size:11px; line-height:1.4; letter-spacing:1.2px; font-weight:700; color:#8e8e93; text-transform:uppercase; font-family:Arial, Helvetica, sans-serif;"
                      >
                        Codigo de verificacao
                      </p>
                    </td>
                  </tr>
                  <tr>
                    <td align="center" style="padding:0 24px 18px 24px;">
                      <p
                        style="margin:0; font-size:36px; line-height:1.2; font-weight:700; letter-spacing:8px; color:#1a1a1e; font-family:Arial, Helvetica, sans-serif;"
                      >
                        {{OTP_CODE}}
                      </p>
                    </td>
                  </tr>
                </table>

                <p
                  style="margin:16px 0 24px 0; font-size:13px; line-height:1.6; text-align:center; color:#4a4a50;"
                >
                  Digite este codigo na tela de confirmacao do app.
                </p>

                <p
                  style="margin:0 0 24px 0; font-size:12px; line-height:1.6; text-align:center; color:#8e8e93;"
                >
                  Se o codigo expirar, solicite um novo envio no aplicativo.
                </p>

                <hr
                  style="border:0; border-top:1px solid #e5e5e5; margin:0 0 20px 0;"
                />

                <p
                  style="margin:0 0 10px 0; font-size:12px; line-height:1.6; text-align:center; color:#8e8e93;"
                >
                  Se voce nao criou uma conta no Animus, ignore este e-mail com
                  seguranca.
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
