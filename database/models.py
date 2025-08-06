from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Table
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# Tabla de asociación para artículos y etiquetas (relación muchos a muchos)
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True)
)

class Article(Base):
    __tablename__ = 'articles'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), unique=True, nullable=False)
    content = Column(Text, nullable=False)
    meta_description = Column(String(160))
    featured_image_url = Column(String(500))
    featured_image_alt = Column(String(255))
    main_keyword = Column(String(100), nullable=False)
    stage = Column(String(20), nullable=False)  # conciencia, consideracion, compra
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    wordpress_id = Column(Integer, unique=True)
    is_published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    category = relationship("Category", back_populates="articles")
    tags = relationship("Tag", secondary=article_tags, back_populates="articles")
    internal_links = relationship("InternalLink", foreign_keys="InternalLink.article_id", back_populates="article")
    cta = relationship("CTA", back_populates="article", uselist=False)

class Category(Base):
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    wordpress_id = Column(Integer, unique=True)
    
    # Relaciones
    articles = relationship("Article", back_populates="category")

class Tag(Base):
    __tablename__ = 'tags'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    slug = Column(String(50), unique=True, nullable=False)
    wordpress_id = Column(Integer, unique=True)
    
    # Relaciones
    articles = relationship("Article", secondary=article_tags, back_populates="tags")

class Keyword(Base):
    __tablename__ = 'keywords'
    
    id = Column(Integer, primary_key=True)
    keyword = Column(String(100), unique=True, nullable=False)
    stage = Column(String(20), nullable=False)  # conciencia, consideracion, compra
    priority = Column(Integer, default=1)  # 1-5, donde 5 es máxima prioridad
    is_used = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class InternalLink(Base):
    __tablename__ = 'internal_links'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    linked_article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    anchor_text = Column(String(255), nullable=False)
    context = Column(Text)  # Contexto donde se coloca el enlace
    
    # Relaciones
    article = relationship("Article", foreign_keys=[article_id], back_populates="internal_links")
    linked_article = relationship("Article", foreign_keys=[linked_article_id])

class CTA(Base):
    __tablename__ = 'ctas'
    
    id = Column(Integer, primary_key=True)
    article_id = Column(Integer, ForeignKey('articles.id'), nullable=False)
    title = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    link_url = Column(String(500), nullable=False)
    stage = Column(String(20), nullable=False)  # conciencia, consideracion, compra
    
    # Relaciones
    article = relationship("Article", back_populates="cta")