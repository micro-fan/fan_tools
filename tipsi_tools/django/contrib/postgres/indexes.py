from django.db.models import Index


class LTreeIndex(Index):

    def create_sql(self, model, schema_editor, using=''):
        """
        Update ltree label path when parent/child relationships changed
        Taken from: https://github.com/peopledoc/django-ltree-demo
        """

        return """
        -- function to calculate the path of any given node
        CREATE OR REPLACE FUNCTION _update_{db_table}_path() RETURNS TRIGGER AS
        $$
        BEGIN
            IF NEW.parent_id IS NULL THEN
                NEW.ltree_label_path = NEW.ltree_label::ltree;
            ELSE
                SELECT ltree_label_path || NEW.ltree_label
                    FROM {db_table}
                    WHERE NEW.parent_id IS NULL or id = NEW.parent_id
                    INTO NEW.ltree_label_path;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;


        -- function to update the path of the descendants of a node
        CREATE OR REPLACE FUNCTION _update_descendants_{db_table}_path() RETURNS TRIGGER AS
        $$
        BEGIN
            UPDATE {db_table}
                SET ltree_label_path =
                    NEW.ltree_label_path ||
                    subpath({db_table}.ltree_label_path, nlevel(OLD.ltree_label_path))
                WHERE {db_table}.ltree_label_path <@ OLD.ltree_label_path AND id != NEW.id;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;


        -- calculate the path every time we insert a new node
        DROP TRIGGER IF EXISTS {db_table}_path_insert_trg ON {db_table};
        CREATE TRIGGER {db_table}_path_insert_trg
            BEFORE INSERT ON {db_table}
            FOR EACH ROW
            EXECUTE PROCEDURE _update_{db_table}_path();


        -- calculate the path when updating the parent or the label
        DROP TRIGGER IF EXISTS {db_table}_path_update_trg ON {db_table};
        CREATE TRIGGER {db_table}_path_update_trg
            BEFORE UPDATE ON {db_table}
            FOR EACH ROW
            WHEN (OLD.parent_id IS DISTINCT FROM NEW.parent_id
                OR OLD.ltree_label IS DISTINCT FROM NEW.ltree_label)
            EXECUTE PROCEDURE _update_{db_table}_path();


        -- if the path was updated, update the path of the descendants
        DROP TRIGGER IF EXISTS {db_table}_path_after_trg ON {db_table};
        CREATE TRIGGER {db_table}_path_after_trg
            AFTER UPDATE ON {db_table}
            FOR EACH ROW
            WHEN (NEW.ltree_label_path IS DISTINCT FROM OLD.ltree_label_path)
            EXECUTE PROCEDURE _update_descendants_{db_table}_path();
        """.format(
            db_table=model._meta.db_table,
        )
