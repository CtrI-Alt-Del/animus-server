EMAIL_VERIFICATION_HTML = """
<!DOCTYPE html>
<html lang="pt-BR">
  <body style="margin:0; padding:0; background-color:#101014; font-family:Arial, Helvetica, sans-serif; color:#FFFFFF;">
    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color:#101014; margin:0; padding:32px 16px;">
      <tr>
        <td align="center">
          <table
            role="presentation"
            width="100%"
            cellspacing="0"
            cellpadding="0"
            style="
              max-width:560px;
              background-color:#1C1C22;
              border:1px solid #2C2C35;
              border-radius:16px;
              padding:40px 32px;
            "
          >
            <tr>
              <td align="center" style="padding-bottom:24px;">
                <h1 style="margin:0; font-size:24px; line-height:32px; color:#FFFFFF; font-weight:700;">
                  Reenvio de confirmação de email
                </h1>
              </td>
            </tr>

            <tr>
              <td style="padding-bottom:16px;">
                <p style="margin:0; font-size:16px; line-height:24px; color:#9CA3AF;">
                  Recebemos uma solicitação para reenviar a confirmação do seu endereço de email.
                </p>
              </td>
            </tr>

            <tr>
              <td style="padding-bottom:24px;">
                <p style="margin:0; font-size:16px; line-height:24px; color:#9CA3AF;">
                  Para confirmar sua conta, clique no botão abaixo:
                </p>
              </td>
            </tr>

            <tr>
              <td align="center" style="padding-bottom:32px;">
                <a
                  href="{verification_url}"
                  style="
                    display:inline-block;
                    background-color:#B58EFF;
                    color:#101014;
                    text-decoration:none;
                    font-size:16px;
                    font-weight:700;
                    padding:14px 24px;
                    border-radius:12px;
                  "
                >
                  Confirmar email
                </a>
              </td>
            </tr>

            <tr>
              <td style="padding-top:24px; border-top:1px solid #2C2C35;">
                <p style="margin:0 0 12px; font-size:14px; line-height:22px; color:#9CA3AF;">
                  Se o botão não funcionar, copie e cole este link no navegador:
                </p>
                <p style="margin:0 0 24px; font-size:14px; line-height:22px; word-break:break-all;">
                  <a href="{verification_url}" style="color:#B58EFF; text-decoration:none;">
                    {verification_url}
                  </a>
                </p>

                <p style="margin:0; font-size:13px; line-height:20px; color:#9CA3AF;">
                  Se você não fez essa solicitação, pode ignorar este email com segurança.
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
