"""Tests for member API routes."""


class TestListMembers:
    """Tests for GET /members endpoint."""

    def test_list_members_empty(self, client_no_auth):
        """Test listing members when database is empty."""
        response = client_no_auth.get("/api/v1/members")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_list_members_with_data(self, client_no_auth, sample_member):
        """Test listing members with data in database."""
        response = client_no_auth.get("/api/v1/members")
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 1
        assert data["total"] == 1
        assert data["items"][0]["member_id"] == sample_member.member_id
        assert data["items"][0]["name"] == sample_member.name
        assert data["items"][0]["callsign"] == sample_member.callsign

    def test_list_members_pagination(self, client_no_auth, sample_member):
        """Test member list pagination parameters."""
        response = client_no_auth.get("/api/v1/members?limit=25&offset=10")
        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 25
        assert data["offset"] == 10

    def test_list_members_requires_read_auth(self, client_with_auth):
        """Test listing members requires read auth when configured."""
        # Without auth header
        response = client_with_auth.get("/api/v1/members")
        assert response.status_code == 401

        # With read key
        response = client_with_auth.get(
            "/api/v1/members",
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 200


class TestGetMember:
    """Tests for GET /members/{member_id} endpoint."""

    def test_get_member_success(self, client_no_auth, sample_member):
        """Test getting a specific member."""
        response = client_no_auth.get(f"/api/v1/members/{sample_member.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == sample_member.member_id
        assert data["name"] == sample_member.name
        assert data["callsign"] == sample_member.callsign
        assert data["role"] == sample_member.role
        assert data["description"] == sample_member.description
        assert data["contact"] == sample_member.contact

    def test_get_member_not_found(self, client_no_auth):
        """Test getting a non-existent member."""
        response = client_no_auth.get("/api/v1/members/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_get_member_requires_read_auth(self, client_with_auth, sample_member):
        """Test getting a member requires read auth when configured."""
        # Without auth header
        response = client_with_auth.get(f"/api/v1/members/{sample_member.id}")
        assert response.status_code == 401

        # With read key
        response = client_with_auth.get(
            f"/api/v1/members/{sample_member.id}",
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 200


class TestCreateMember:
    """Tests for POST /members endpoint."""

    def test_create_member_success(self, client_no_auth):
        """Test creating a new member."""
        response = client_no_auth.post(
            "/api/v1/members",
            json={
                "member_id": "bob",
                "name": "Bob Jones",
                "callsign": "W2XYZ",
                "role": "Member",
                "description": "Regular member",
                "contact": "bob@example.com",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["member_id"] == "bob"
        assert data["name"] == "Bob Jones"
        assert data["callsign"] == "W2XYZ"
        assert data["role"] == "Member"
        assert "id" in data
        assert "created_at" in data

    def test_create_member_minimal(self, client_no_auth):
        """Test creating a member with only required fields."""
        response = client_no_auth.post(
            "/api/v1/members",
            json={
                "member_id": "charlie",
                "name": "Charlie Brown",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["member_id"] == "charlie"
        assert data["name"] == "Charlie Brown"
        assert data["callsign"] is None
        assert data["role"] is None

    def test_create_member_duplicate_member_id(self, client_no_auth, sample_member):
        """Test creating a member with duplicate member_id fails."""
        response = client_no_auth.post(
            "/api/v1/members",
            json={
                "member_id": sample_member.member_id,  # "alice" already exists
                "name": "Another Alice",
            },
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_create_member_requires_admin_auth(self, client_with_auth):
        """Test creating a member requires admin auth."""
        # Without auth
        response = client_with_auth.post(
            "/api/v1/members",
            json={"member_id": "test", "name": "Test User"},
        )
        assert response.status_code == 401

        # With read key (not admin)
        response = client_with_auth.post(
            "/api/v1/members",
            json={"member_id": "test", "name": "Test User"},
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 403

        # With admin key
        response = client_with_auth.post(
            "/api/v1/members",
            json={"member_id": "test", "name": "Test User"},
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == 201


class TestUpdateMember:
    """Tests for PUT /members/{member_id} endpoint."""

    def test_update_member_success(self, client_no_auth, sample_member):
        """Test updating a member."""
        response = client_no_auth.put(
            f"/api/v1/members/{sample_member.id}",
            json={
                "name": "Alice Johnson",
                "role": "Super Admin",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Alice Johnson"
        assert data["role"] == "Super Admin"
        # Unchanged fields should remain
        assert data["member_id"] == sample_member.member_id
        assert data["callsign"] == sample_member.callsign

    def test_update_member_change_member_id(self, client_no_auth, sample_member):
        """Test updating member_id."""
        response = client_no_auth.put(
            f"/api/v1/members/{sample_member.id}",
            json={"member_id": "alice2"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["member_id"] == "alice2"

    def test_update_member_member_id_collision(
        self, client_no_auth, api_db_session, sample_member
    ):
        """Test updating member_id to one that already exists fails."""
        from meshcore_hub.common.models import Member

        # Create another member
        other_member = Member(
            member_id="bob",
            name="Bob",
        )
        api_db_session.add(other_member)
        api_db_session.commit()

        # Try to change alice's member_id to "bob"
        response = client_no_auth.put(
            f"/api/v1/members/{sample_member.id}",
            json={"member_id": "bob"},
        )
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"].lower()

    def test_update_member_not_found(self, client_no_auth):
        """Test updating a non-existent member."""
        response = client_no_auth.put(
            "/api/v1/members/nonexistent-id",
            json={"name": "New Name"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_update_member_requires_admin_auth(self, client_with_auth, sample_member):
        """Test updating a member requires admin auth."""
        # Without auth
        response = client_with_auth.put(
            f"/api/v1/members/{sample_member.id}",
            json={"name": "New Name"},
        )
        assert response.status_code == 401

        # With read key (not admin)
        response = client_with_auth.put(
            f"/api/v1/members/{sample_member.id}",
            json={"name": "New Name"},
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 403

        # With admin key
        response = client_with_auth.put(
            f"/api/v1/members/{sample_member.id}",
            json={"name": "New Name"},
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == 200


class TestDeleteMember:
    """Tests for DELETE /members/{member_id} endpoint."""

    def test_delete_member_success(self, client_no_auth, sample_member):
        """Test deleting a member."""
        response = client_no_auth.delete(f"/api/v1/members/{sample_member.id}")
        assert response.status_code == 204

        # Verify it's deleted
        response = client_no_auth.get(f"/api/v1/members/{sample_member.id}")
        assert response.status_code == 404

    def test_delete_member_not_found(self, client_no_auth):
        """Test deleting a non-existent member."""
        response = client_no_auth.delete("/api/v1/members/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_delete_member_requires_admin_auth(self, client_with_auth, sample_member):
        """Test deleting a member requires admin auth."""
        # Without auth
        response = client_with_auth.delete(f"/api/v1/members/{sample_member.id}")
        assert response.status_code == 401

        # With read key (not admin)
        response = client_with_auth.delete(
            f"/api/v1/members/{sample_member.id}",
            headers={"Authorization": "Bearer test-read-key"},
        )
        assert response.status_code == 403

        # With admin key
        response = client_with_auth.delete(
            f"/api/v1/members/{sample_member.id}",
            headers={"Authorization": "Bearer test-admin-key"},
        )
        assert response.status_code == 204
