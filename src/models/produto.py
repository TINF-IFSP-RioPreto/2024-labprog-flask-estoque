import io
import uuid
from base64 import b64decode

from PIL import Image

from sqlalchemy import Boolean, DECIMAL, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import mapped_column, relationship
from src.modules import db
from src.models.base_mixin import BasicRepositoryMixin, TimeStampMixin

class Produto(db.Model, BasicRepositoryMixin, TimeStampMixin):
    __tablename__ = 'produtos'
    id = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    nome = mapped_column(String(100), nullable=False, index=True)
    preco = mapped_column(DECIMAL(10, 2), default=0.00, nullable=False)
    estoque = mapped_column(Integer, default=0)
    ativo = mapped_column(Boolean, default=True, nullable=False)
    possui_foto = mapped_column(Boolean, default=False, nullable=False)
    foto_base64 = mapped_column(Text, default=None, nullable=True)
    foto_mime = mapped_column(String(64), nullable=True, default=None)
    categoria_id = mapped_column(Uuid(as_uuid=True), ForeignKey('categorias.id'))

    categoria = relationship('Categoria',
                             back_populates='lista_de_produtos')

    @property
    def imagem(self):
        if not self.possui_foto:
            saida = io.BytesIO()
            entrada = Image.new('RGB', (200, 200), (255, 0, 0))
            formato = "PNG"
            entrada.save(saida, format=formato)
            conteudo = saida.getvalue()
            tipo = 'image/png'
        else:
            conteudo = b64decode(self.foto_base64)
            tipo = self.foto_mime
        return conteudo, tipo


    def thumbnail(self, size: int = 128):
        if not self.possui_foto:
            ...
        else:
            arquivo = io.BytesIO(b64decode(self.foto_base64))
            saida = io.BytesIO()
            entrada = Image.open(arquivo)
            formato = entrada.format
            (largura, altura) = entrada.size
            fator = min(size/largura, size/altura)
            novo_tamanho = (int(largura * fator), int(altura * fator))
            entrada.thumbnail(novo_tamanho)
            entrada.save(saida, format=formato)
            conteudo = saida.getvalue()
            tipo = self.foto_mime
        return conteudo, tipo
