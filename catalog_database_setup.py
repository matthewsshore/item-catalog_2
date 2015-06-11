from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class UserList(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250), nullable=False)


class CatalogTitles(Base):
    __tablename__ = 'catalog'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    owner_id = Column(Integer, ForeignKey('user.id'))
    owner_name = Column(String(250), ForeignKey('user.name'))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'title': self.title,
            'id': self.id,
            }


class ListItems(Base):
    __tablename__ = 'itemList'

    id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey('catalog.id'))
    category = relationship(CatalogTitles)
    name = Column(String(250), nullable=False)
    description = Column(String(250), nullable=False)
    picture = Column(String(250), nullable=False)
    owner_id = Column(Integer, ForeignKey('user.id'))
    owner_name = Column(String(250), ForeignKey('user.name'))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'name': self.name,
            'id': self.id,
            'description': self.description,
            'picture': self.picture,
        }

engine = create_engine('sqlite:///catalogDatabase.db')


Base.metadata.create_all(engine)
