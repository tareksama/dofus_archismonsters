from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
    Table,
    create_engine,
    func,
    select,
    update,
    delete
)
from sqlalchemy.orm import relationship, sessionmaker, declarative_base


Base = declarative_base()

# Association table to hold quantity of each monster per user
user_monsters = Table(
    'user_monsters',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('monster_id', Integer, ForeignKey('monsters.id'), primary_key=True),
    Column('quantity', Integer, nullable=False, default=1)
)



class Monster(Base):
    __tablename__ = 'monsters'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    step = Column(Integer, nullable=False)  # values 1 -> 35
    level = Column(String(30), nullable=False, unique=False)
    zone = Column(String(50), nullable=False, unique=False)

    def __repr__(self):
        return f"<Monster(id={self.id}, name='{self.name}', step={self.step})>"

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False, unique=True)
    password = Column(String(255), nullable=False, unique=True)

    monsters = relationship(
        "Monster",
        secondary=user_monsters,
        backref="owners",
        lazy='joined'
    )

    def __repr__(self):
        return f"<User(id={self.id}, name='{self.name}', pass='{self.password}')>"

class Database:
    def __init__(self, url="postgresql://postgres.wnpcfgcpeozbpypascub:tarik-258654@aws-0-eu-north-1.pooler.supabase.com:5432/postgres"):
        self.engine = create_engine(url, echo=True)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)

    def get_session(self):
        return self.Session()

    def add_user(self, name):
        session = self.get_session()
        user = User(name=name)
        session.add(user)
        session.commit()
        session.close()
        return user
    
    def get_user_by_name(self, name):
        session = self.get_session()
        user = session.query(User).filter_by(name=name).first()
        session.close()
        return user
    
    def add_monster(self, name, step, level, zone):
        if not (1 <= step <= 35):
            raise ValueError("Step must be between 1 and 35.")
        session = self.get_session()
        monster = Monster(name=name, step=step, level=level, zone=zone)
        session.add(monster)
        session.commit()
        session.close()
        return monster
    
    def get_monster_by_name(self, name):
        session = self.get_session()
        monster = session.query(Monster).filter_by(name=name).first()
        session.close()
        return monster
    
    def get_user_monsters(self, user_name):
        session = self.get_session()
        try:
            # Get the user first
            user = session.query(User).filter_by(name=user_name).first()
            if not user:
                return []

            # LEFT OUTER JOIN to get all monsters and their quantity (if any)
            results = (
                session.query(Monster, user_monsters.c.quantity)
                .outerjoin(user_monsters, (Monster.id == user_monsters.c.monster_id) & (user_monsters.c.user_id == user.id))
                .all()
            )

            monsters = []
            for monster, quantity in results:
                monster.quantity = quantity if quantity is not None else 0
                monsters.append(monster)

            session.expunge_all()
            return monsters
        finally:
            session.close()


    def update_user_monster_quantity(self, user_id, monster_ids, delta):
        """
        Increment or decrement quantity of multiple monsters owned by a user.

        Args:
            user_id: ID of the user.
            monster_ids: List of monster IDs.
            delta: Integer (positive to increment, negative to decrement).
        """
        session = self.get_session()
        conn = session.connection()

        for monster_id in monster_ids:
            # Try to find existing row
            existing = conn.execute(
                select(user_monsters)
                .where(user_monsters.c.user_id == user_id)
                .where(user_monsters.c.monster_id == monster_id)
            ).first()

            if existing is None:
                if delta > 0:
                    # Insert new row if delta positive
                    conn.execute(
                        user_monsters.insert().values(
                            user_id=user_id,
                            monster_id=monster_id,
                            quantity=delta
                        )
                    )
                # If delta is negative and row doesn't exist, skip
            else:
                current_qty = existing.quantity
                new_qty = current_qty + delta

                if new_qty > 0:
                    # Update quantity
                    conn.execute(
                        update(user_monsters)
                        .where(user_monsters.c.user_id == user_id)
                        .where(user_monsters.c.monster_id == monster_id)
                        .values(quantity=new_qty)
                    )
                else:
                    # Delete row if quantity becomes zero or less
                    conn.execute(
                        delete(user_monsters)
                        .where(user_monsters.c.user_id == user_id)
                        .where(user_monsters.c.monster_id == monster_id)
                    )

        session.commit()
        session.close()


    
    def get_monsters(self):
        session = self.get_session()
        monsters = session.query(Monster).all()
        session.expunge_all()  # Detach so they can be accessed after session close
        session.close()
        return monsters
    
    def get_monsters_by_name(self, name):
        session = self.get_session()
        try:
            monsters = (
                session.query(Monster)
                .filter(func.lower(Monster.name).like(f"%{name.lower()}%"))
                .all()
            )
            session.expunge_all()  # Detach objects so they can be accessed after session close
            return monsters
        finally:
            session.close()

    def add_monster_to_user(self, user_id, monster_id, quantity):
        session = self.get_session()
        conn = session.connection()
        conn.execute(user_monsters.insert().values(
            user_id=user_id,
            monster_id=monster_id,
            quantity=quantity
        ))
        session.commit()
        session.close()

# --- Usage Example ---
if __name__ == "__main__":
    db = Database()

    # # Link monster to user with quantity
    db.add_monster_to_user(1, 2, 3)
    db.add_monster_to_user(1, 12, 1)
    db.add_monster_to_user(1, 20, 5)
    db.add_monster_to_user(1, 13, 2)
    db.add_monster_to_user(1, 29, 0)

    print("User and monster created successfully!")
